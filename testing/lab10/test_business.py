import sqlite3

import pytest
from pydantic import ValidationError

from coffeedesk.database import Database
from coffeedesk.errors import DomainError
from coffeedesk.repository import Repository


def test_create_defaults_and_author(service, users, payload):
    item = service.create(users["barista1"], payload)
    assert item["applicant_id"] == 5
    assert item["status_code"] == "new"
    assert item["assignee_id"] is None
    assert item["number"] == f"CB-{item['id']:05d}"
    assert service.history(users["admin"], item["id"])[0]["event"] == "created"


def test_persistent_update_new_connection(service, database, users, payload):
    item = service.create(users["barista1"], payload)
    service.update(users["barista1"], item["id"], {"priority": "urgent"})
    from coffeedesk.services import RequestService

    assert RequestService(Database(database.path)).get(users["admin"], item["id"])["priority"] == "urgent"


def test_full_status_workflow(service, users, payload):
    item = service.create(users["barista1"], payload)
    service.assign(users["operator"], item["id"], 3)
    service.change_status(users["tech1"], item["id"], "in_progress")
    service.change_status(users["tech1"], item["id"], "done")
    service.change_status(users["operator"], item["id"], "closed")
    assert service.get(users["admin"], item["id"])["status_code"] == "closed"
    history = service.history(users["admin"], item["id"])
    assert [event["new_value"] for event in history if event["event"] == "status_changed"] == ["in_progress", "done", "closed"]


def test_start_requires_assignee(service, users):
    with pytest.raises(DomainError) as error:
        service.change_status(users["admin"], 1, "in_progress")
    assert error.value.status == 409
    assert service.get(users["admin"], 1)["status_code"] == "new"


def test_status_skip_is_rejected(service, users):
    with pytest.raises(DomainError) as error:
        service.change_status(users["admin"], 1, "done")
    assert error.value.status == 409


def test_idempotent_status_does_not_duplicate_audit(service, users):
    before = len(service.history(users["admin"], 1))
    service.change_status(users["admin"], 1, "new")
    assert len(service.history(users["admin"], 1)) == before


@pytest.mark.parametrize("assignee", [1, 5, 999999])
def test_assignment_requires_real_technician(service, users, assignee):
    with pytest.raises(DomainError) as error:
        service.assign(users["admin"], 1, assignee)
    assert error.value.status == 422


def test_cannot_remove_assignee_in_progress(service, users):
    with pytest.raises(DomainError) as error:
        service.assign(users["admin"], 3, None)
    assert error.value.status == 409


def test_technician_cannot_close(service, users):
    with pytest.raises(DomainError) as error:
        service.change_status(users["tech1"], 4, "closed")
    assert error.value.status == 403


def test_applicant_own_new_only(service, users):
    with pytest.raises(DomainError) as error:
        service.update(users["barista1"], 3, {"priority": "urgent"})
    assert error.value.status == 403
    with pytest.raises(DomainError) as error:
        service.get(users["barista1"], 2)
    assert error.value.status == 404


def test_closed_request_is_immutable(service, users):
    with pytest.raises(DomainError) as error:
        service.update(users["admin"], 12, {"priority": "low"})
    assert error.value.status == 409


def test_archive_confirmation_role_and_state(service, users):
    for user, identifier, confirm, expected in [("operator",12,True,403),("admin",12,False,400),("admin",1,True,409)]:
        with pytest.raises(DomainError) as error:
            service.archive(users[user], identifier, confirmed=confirm)
        assert error.value.status == expected


def test_archive_is_non_destructive_and_idempotent(service, users):
    service.archive(users["admin"], 12, confirmed=True)
    service.archive(users["admin"], 12, confirmed=True)
    assert service.get(users["admin"], 12)["archived"] is True
    assert service.comments(users["admin"], 12)
    assert sum(event["event"] == "archived" for event in service.history(users["admin"],12)) == 1
    assert all(item["id"] != 12 for item in service.list(users["admin"]))


def test_audit_failure_rolls_back_request(service, database, users, payload, monkeypatch):
    def fail(*args, **kwargs):
        raise sqlite3.OperationalError("injected audit write failure")

    monkeypatch.setattr(Repository, "add_history", fail)
    with pytest.raises(sqlite3.OperationalError):
        service.create(users["barista1"], payload)
    with database.transaction() as con:
        # This assert detects an incorrectly committed request without its audit.
        assert con.execute("SELECT COUNT(*) FROM Requests").fetchone()[0] == 12


def test_unicode_search_and_combined_filters(service, users):
    items = service.list(users["admin"], q="КРАН", status_code="new", category_id=1)
    assert [item["id"] for item in items] == [1]


def test_search_wildcards_and_sql_injection_are_literal(service, users, payload):
    item = service.create(users["admin"], dict(payload,title="Скидка 100% для SQL-теста"))
    assert [row["id"] for row in service.list(users["admin"],q="%")] == [item["id"]]
    assert service.list(users["admin"],q="' OR 1=1 --") == []


def test_comment_trim_and_empty_rejection(service, users):
    comment = service.add_comment(users["barista1"], 1, {"body": "  Уточнение  "})
    assert comment["body"] == "Уточнение"
    with pytest.raises(ValidationError):
        service.add_comment(users["barista1"], 1, {"body": "   "})


def test_foreign_key_and_catalog_validation(service, users, payload):
    with pytest.raises(DomainError) as error:
        service.create(users["admin"],dict(payload,category_id=99999))
    assert error.value.status == 422
