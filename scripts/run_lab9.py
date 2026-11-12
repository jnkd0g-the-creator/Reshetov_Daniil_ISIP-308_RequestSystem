"""30 real browser/HTTP/SQLite cases. Does not pretend to be student manual work."""

import csv
import json
import sqlite3
from pathlib import Path

import httpx
from browser_support import configure_browser
from check_api import run as curl_check
from playwright.sync_api import expect, sync_playwright
from test_environment import isolated_server

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "testing/lab9"
PAYLOAD = {"title": "Проверка API", "description": "Подробное учебное описание для проверки HTTP и SQLite.", "cafe_id": 1, "category_id": 1}


def main():
    configure_browser()
    evidence = OUT / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    results, requests = [], []
    with isolated_server(OUT) as (base, settings, credentials, credentials_path), sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1050})
        clients = {}

        def client(username="admin"):
            if username not in clients:
                connection = httpx.Client(base_url=base)
                response = connection.post("/auth/login", json={"username": username, "password": credentials[username]})
                assert response.status_code == 200
                connection.headers["X-CSRF-Token"] = response.json()["csrf_token"]
                clients[username] = connection
            return clients[username]

        def api(method, path, expected=200, body=None, username="admin", headers=None):
            response = client(username).request(method, path, json=body, headers=headers)
            requests.append({"method": method, "path": path, "expected": expected, "actual": response.status_code, "body": body, "response": response.json() if response.content else None})
            assert response.status_code == expected, f"{method} {path}: expected {expected}, got {response.status_code}"
            return response

        def sql(query, params=()):
            with sqlite3.connect(settings.db_path) as con:
                return con.execute(query, params).fetchall()

        def ui_login(username):
            page.context.clear_cookies()
            page.goto(base)
            page.evaluate("sessionStorage.clear()")
            page.reload()
            page.get_by_label("Логин").fill(username)
            page.get_by_label("Пароль").fill(credentials[username])
            page.get_by_role("button", name="Войти →").click()
            page.get_by_role("heading", name="Заявки кофе-баров").wait_for()

        def ui_open(hash, title):
            page.goto(base + "/#" + hash)
            page.get_by_role("heading", name=title, exact=True).wait_for()

        def ui_create(title, description=PAYLOAD["description"]):
            ui_open("new", "Новая заявка")
            page.get_by_label("Тема заявки").fill(title)
            page.get_by_label("Описание *").fill(description)
            page.get_by_role("button", name="Создать заявку", exact=True).click()
            page.get_by_role("heading", name=title, exact=True).wait_for()
            return int(page.url.split("#requests/")[1])

        def case(number, group, goal, steps, data, expected, function, mode="browser + SQLite"):
            identifier = f"TC-{number:02d}"
            try:
                actual = function()
                status = "PASS"
            except Exception as exc:
                actual, status = f"{type(exc).__name__}: {exc}", "FAIL"
            # Password fields are never recorded as text; login requests are never retained.
            image = evidence / f"{identifier}.png"
            page.screenshot(path=str(image))
            trace = {"id": identifier, "expected": expected, "actual": actual, "status": status, "execution_mode": mode, "related_http": requests[-5:]}
            (evidence / f"{identifier}.json").write_text(json.dumps(trace, ensure_ascii=False, indent=2) + "\n")
            results.append({"id": identifier, "group": group, "goal": goal, "preconditions": "Отдельная seed-БД, действующая учётная запись указанной роли; исходно 12 заявок.", "steps": steps, "input": data, "expected": expected, "actual": actual, "status": status, "evidence": f"evidence/{identifier}.json; evidence/{identifier}.png", "execution_mode": mode, "manual_status": "BLOCKED"})
            print(identifier, status, goal)

        state = {}
        ui_login("admin")

        def create():
            state["ui"] = ui_create("Протекает контрольный кран")
            assert sql("SELECT title FROM Requests WHERE id=?", (state["ui"],))[0][0] == "Протекает контрольный кран"
            return f"Создана форма, id={state['ui']}; строка реально в SQLite."
        case(1,"positive/integration","Создание формы", "Войти admin → Новая → ввести поля → Создать → проверить SQLite", "Тема=Протекает контрольный кран; описание ≥10; бар=1; категория=1", "Карточка с номером, строка SQLite, new", create)

        def view():
            ui_open("requests", "Заявки кофе-баров")
            page.get_by_role("link", name="Протекает контрольный кран", exact=True).click()
            expect(page.locator(".badge.new")).to_be_visible()
            return "Список → карточка, отображены реквизиты и Новая."
        case(2,"positive","Список и карточка", "Открыть список → выбрать созданную", "Заявка TC-01", "Открыта правильная карточка", view)

        def search():
            ui_open("requests", "Заявки кофе-баров")
            page.get_by_label("Поиск по номеру, теме или описанию").fill("КОНТРОЛЬНЫЙ")
            page.get_by_label("Статус", exact=True).select_option("new")
            page.get_by_label("Категория", exact=True).select_option("1")
            page.get_by_role("button", name="Найти", exact=True).click()
            expect(page.locator("tbody tr")).to_have_count(1)
            return "Кириллица верхнего регистра + статус + категория: одна нужная строка."
        case(3,"positive","Поиск и пересечение фильтров", "Ввести КОНТРОЛЬНЫЙ, выбрать new/сантехника → Найти", "q=КОНТРОЛЬНЫЙ; status=new; category=1", "Одна соответствующая строка, регистр не важен", search)

        def edit():
            ui_open(f"requests/{state['ui']}/edit", "Редактирование заявки")
            page.get_by_label("Описание *").fill("Описание уточнено: заменить уплотнение контрольного крана.")
            page.get_by_role("button", name="Сохранить изменения").click()
            expect(page.get_by_text("Описание уточнено:", exact=False)).to_be_visible()
            assert "уточнено" in sql("SELECT description FROM Requests WHERE id=?", (state["ui"],))[0][0]
            return "Изменение видно в карточке и SQLite."
        case(4,"positive/integration","Редактирование", "Открыть редактирование → изменить описание → сохранить", "Уточнённое описание ≥10 символов", "Новое описание сохранено", edit)

        def start():
            page.get_by_label("Назначение").select_option("3")
            page.get_by_role("button", name="Назначить", exact=True).click()
            expect(page.locator(".meta")).to_contain_text("Мастер 1")
            page.get_by_role("button", name="Взять в работу").click()
            expect(page.locator(".badge.in_progress")).to_be_visible()
            return "Мастер 1 назначен, статус В работе."
        case(5,"positive","Назначение и смена статуса", "Назначить tech1 → Взять в работу", "assignee=3, next=in_progress", "Мастер и В работе сохранены", start)

        def empty_title():
            before = sql("SELECT COUNT(*) FROM Requests")[0][0]
            ui_open("new", "Новая заявка")
            page.get_by_label("Описание *").fill(PAYLOAD["description"])
            page.get_by_role("button", name="Создать заявку", exact=True).click()
            assert page.get_by_label("Тема заявки").evaluate("e => e.validity.valueMissing")
            assert sql("SELECT COUNT(*) FROM Requests")[0][0] == before
            return "Браузер остановил пустое обязательное поле, строка не создана."
        case(6,"negative","Пустая тема", "Оставить тему пустой → отправить", "title=пусто", "Форма не отправлена, БД без изменений", empty_title)

        def boolean_id():
            before = sql("SELECT COUNT(*) FROM Requests")[0][0]
            api("POST","/requests",422,dict(PAYLOAD,cafe_id=True))
            assert sql("SELECT COUNT(*) FROM Requests")[0][0] == before
            return "422, число строк не изменилось; BUG-01 не воспроизводится."
        case(7,"negative/regression/API","BUG-01: неверный тип ID", "POST с JSON boolean вместо cafe_id", "cafe_id=true", "422 без создания", boolean_id,"HTTP + SQLite")

        def absent():
            ui_open("requests/99999999", "Не удалось открыть страницу")
            expect(page.get_by_role("alert")).to_contain_text("не найдена")
            api("GET","/requests/99999999",404)
            return "UI показал понятную ошибку, HTTP 404."
        case(8,"negative/API","Отсутствующая заявка", "Открыть ID 99999999 в UI и API", "id=99999999", "Понятная ошибка и 404", absent)

        def skip_status():
            api("PATCH",f"/requests/{state['ui']}/status",409,{"status_code":"closed"})
            assert sql("SELECT status_code FROM Requests WHERE id=?",(state["ui"],))[0][0] == "in_progress"
            return "409, статус остался in_progress."
        case(9,"negative","Запрещённый скачок статуса", "В работе → сразу Закрыта через API", "status_code=closed", "409, состояние не изменено", skip_status,"HTTP + SQLite")

        def min_title():
            value = ui_create("Кра")
            assert len(sql("SELECT title FROM Requests WHERE id=?",(value,))[0][0]) == 3
            return "Тема 3 символа сохранена."
        case(10,"boundary","Минимум темы", "Создать через форму тему из 3 символов", "title=Кра", "Создано, длина 3", min_title)

        def max_title():
            value = ui_create("К"*120)
            assert len(sql("SELECT title FROM Requests WHERE id=?",(value,))[0][0]) == 120
            return "120 символов сохранены без усечения."
        case(11,"boundary","Максимум темы", "Создать через форму тему 120 символов", "title=К × 120", "Создано, длина 120", max_title)

        def max_description():
            value = ui_create("Граница описания", "Д"*4000)
            assert len(sql("SELECT description FROM Requests WHERE id=?",(value,))[0][0]) == 4000
            return "4000 символов сохранены."
        case(12,"boundary","Максимум описания", "Ввести 4000 символов описания в форму", "description=Д × 4000", "Создано, длина 4000", max_description)

        def applicant():
            ui_login("barista1")
            assert page.locator('a[href="#requests/2"]').count() == 0
            items=api("GET","/requests",username="barista1").json()
            assert items and all(item["applicant_id"]==5 for item in items)
            return "В UI нет чужой CB-00002; все API-объекты автора 5."
        case(13,"roles","Заявитель видит только свои", "Войти barista1 → открыть список → сравнить авторов", "barista1; чужая seed-заявка 2", "Нет чужих объектов", applicant)

        def technician():
            ui_login("tech1")
            assert page.get_by_role("link",name="＋ Создать заявку",exact=True).count() == 0
            api("POST","/requests",403,PAYLOAD,username="tech1")
            return "Кнопки создания нет; прямой POST тоже запрещён 403."
        case(14,"roles/negative","Исполнителю запрещено создание", "Войти tech1 → проверить UI → прямой POST", "role=technician", "Кнопка скрыта, POST 403", technician)

        def atomic_create():
            ui_login("admin")
            value=ui_create("Интеграция формы и аудита")
            assert sql("SELECT event,new_value FROM RequestHistory WHERE request_id=?",(value,)) == [("created","new")]
            return f"UI создал id={value}; ровно одна история created/new в SQLite."
        case(15,"integration","Форма + БД + аудит", "Создать новую через UI → SQL Requests и History", "Тема=Интеграция формы и аудита", "Заявка и история созданы вместе", atomic_create)

        def atomic_status():
            ui_open(f"requests/{state['ui']}","Протекает контрольный кран")
            page.get_by_role("button",name="Отметить выполнение").click()
            expect(page.locator(".badge.done")).to_be_visible()
            assert sql("SELECT status_code FROM Requests WHERE id=?",(state["ui"],)) == [("done",)]
            assert sql("SELECT new_value FROM RequestHistory WHERE request_id=? AND event='status_changed' ORDER BY id DESC LIMIT 1",(state["ui"],)) == [("done",)]
            return "UI Выполнена = SQLite done = последняя история done."
        case(16,"integration/positive","Статус + БД + история", "Отметить выполнение в UI → проверить обе таблицы", "Заявка TC-01 в работе", "Три компонента согласованы", atomic_status)

        def get_api():
            data=api("GET","/requests").json()
            assert isinstance(data,list) and len(data)>=12
            return f"200, JSON-массив {len(data)} объектов."
        case(17,"API","GET списка", "GET /requests с сессией", "limit по умолчанию", "200 и JSON-массив", get_api,"HTTP")

        def post_api():
            response=api("POST","/requests",201,PAYLOAD)
            state["api"]=response.json()["id"]
            assert response.headers["Location"] == f"/requests/{state['api']}"
            return f"201, id={state['api']}, корректный Location."
        case(18,"API","POST и Location", "POST валидного JSON", "PAYLOAD из scripts/run_lab9.py", "201 + созданный объект + Location", post_api,"HTTP")

        def patch_api():
            api("PATCH",f"/requests/{state['api']}",200,{"priority":"urgent"})
            assert api("GET",f"/requests/{state['api']}").json()["priority"] == "urgent"
            return "PATCH 200, повторный GET priority=urgent."
        case(19,"API/integration","PATCH и повторное чтение", "PATCH priority → GET объекта", "priority=urgent", "Изменение действительно сохранено", patch_api,"HTTP")

        def delete_api():
            path=f"/requests/{state['api']}"
            api("PATCH",path+"/assignment",200,{"assignee_id":3})
            for status in ["in_progress","done","closed"]:
                api("PATCH",path+"/status",200,{"status_code":status})
            response=api("DELETE",path+"?confirm=true",204)
            assert response.content == b""
            assert sql("SELECT archived FROM Requests WHERE id=?",(state["api"],)) == [(1,)]
            return "204 без тела; archived=1, бизнес-строка не удалена."
        case(20,"API","DELETE-архив", "Назначить → все статусы → DELETE confirm=true → SQL", "Закрытая заявка TC-18; admin", "204, архив и сохранённая история", delete_api,"HTTP + SQLite")

        def csrf_fail():
            api("POST","/requests",403,PAYLOAD,headers={"X-CSRF-Token":""})
            return "403 csrf_failed без корректного заголовка."
        case(21,"roles/negative","CSRF", "POST с cookie, но пустым CSRF", "X-CSRF-Token отсутствует", "403", csrf_fail,"HTTP")

        def empty():
            ui_open("requests?q=NO_MATCH_COFFEEDESK_999", "Заявки кофе-баров")
            expect(page.get_by_role("heading",name="Заявок не найдено")).to_be_visible()
            page.get_by_role("button",name="Сбросить фильтры").click()
            expect(page.locator("tbody tr").first).to_be_visible()
            return "Пустое состояние понятно, сброс возвращает строки."
        case(22,"boundary/positive","Пустой поиск и сброс", "Искать отсутствующую строку → Сбросить", "q=NO_MATCH_COFFEEDESK_999", "Пусто, затем список", empty)

        def whitespace():
            ui_open("new","Новая заявка")
            page.get_by_label("Тема заявки").fill("   ")
            page.get_by_label("Описание *").fill(PAYLOAD["description"])
            page.get_by_role("button",name="Создать заявку",exact=True).click()
            expect(page.get_by_role("alert")).to_contain_text("Проверьте обязательные поля")
            assert page.get_by_label("Описание *").input_value()==PAYLOAD["description"]
            return "Сервер отклонил тему после trim, введённое описание не потерялось."
        case(23,"negative","Пробелы и сохранение формы", "Отправить тему из пробелов", "title=три пробела", "Ошибка без очистки описания", whitespace)

        def unauthenticated():
            response=httpx.get(base+"/requests")
            assert response.status_code==401 and response.json()["error"]["code"]=="unauthenticated"
            return "401 unauthenticated, данных заявок нет."
        case(24,"roles/API","Без авторизации", "GET без cookie", "анонимный запрос", "401", unauthenticated,"HTTP")

        def hidden():
            api("GET","/requests/2",404,username="barista1")
            return "Чужая существующая заявка скрыта тем же 404, что отсутствующая."
        case(25,"roles/negative","Скрытие чужого объекта", "barista1 запрашивает чужую seed-заявку 2", "id=2", "404 без утечки", hidden,"HTTP")

        def xss():
            title='<img src=x onerror="window.xss=1">'
            value=ui_create(title)
            assert page.locator('h1 img').count()==0 and page.evaluate("window.xss || 0")==0
            assert sql("SELECT title FROM Requests WHERE id=?",(value,))[0][0]==title
            return "Спецсимволы сохранены, отрисованы текстом; img/обработчик не исполнены."
        case(26,"boundary/security","HTML как текст", "Создать тему с img/onerror → проверить DOM и SQL", "title=<img src=x onerror=window.xss=1>", "Текст, без выполнения JavaScript", xss)

        def too_long():
            api("POST","/requests",422,dict(PAYLOAD,description="Д"*4001))
            return "422 при 4001 символе."
        case(27,"boundary/negative","Превышение описания", "POST описания 4001 символ", "description=Д × 4001", "422", too_long,"HTTP")

        def cancel_archive():
            ui_open("requests/12","Заменить уплотнение холодильника")
            page.get_by_role("button",name="Архивировать заявку").click()
            expect(page.get_by_role("dialog")).to_be_visible()
            page.get_by_role("button",name="Отмена",exact=True).click()
            assert sql("SELECT archived FROM Requests WHERE id=12") == [(0,)]
            return "Диалог закрыт, archived=0; отмена не меняет данные."
        case(28,"positive/integration","Отмена опасного действия", "Архив закрытой → Отмена → SQLite", "seed-заявка 12, admin", "Не архивирована", cancel_archive)

        def comment():
            page.get_by_label("Новый комментарий").fill("Результат проверен тестовым сценарием.")
            page.get_by_role("button",name="Отправить",exact=True).click()
            expect(page.get_by_text("Результат проверен тестовым сценарием.",exact=True)).to_be_visible()
            assert sql("SELECT COUNT(*) FROM Comments WHERE request_id=12 AND body=?",("Результат проверен тестовым сценарием.",))[0][0]==1
            return "Комментарий отображён и однажды записан в SQLite."
        case(29,"positive/integration","Комментарий", "Добавить комментарий через UI → SQL", "Тестовый текст без персональных данных", "В UI и БД одинаковый текст", comment)

        def invalid_enum():
            api("POST","/requests",422,dict(PAYLOAD,priority="maximum"))
            api("PATCH","/requests/1/status",422,{"status_code":"broken"})
            return "Неизвестные priority и status отклонены 422."
        case(30,"negative/API","Недопустимые значения", "POST с priority maximum; PATCH status broken", "maximum / broken", "Оба 422", invalid_enum,"HTTP")

        # Independent real curl collection on this same isolated version and data.
        curl_check(base, credentials_path, OUT / "api")
        for connection in clients.values():
            connection.close()
        browser.close()
    keys=list(results[0])
    with (OUT / "test_cases.csv").open("w",encoding="utf-8-sig",newline="") as file:
        writer=csv.DictWriter(file,fieldnames=keys,delimiter=";")
        writer.writeheader();writer.writerows(results)
    (OUT / "http_results.json").write_text(json.dumps(requests,ensure_ascii=False,indent=2)+"\n")
    totals={status:sum(row["status"]==status for row in results) for status in ["PASS","FAIL","BLOCKED"]}
    summary={"total":len(results),**totals,"manual_review":"BLOCKED (not performed by student)","remote":"BLOCKED"}
    (OUT / "results.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n")
    table="\n".join(f"| {row['id']} | {row['goal']} | {row['status']} | {row['actual']} |" for row in results)
    (OUT / "results.md").write_text("# Фактические результаты инструментального прогона\n\nЭто браузерная/HTTP-автоматизация агента, не ручной прогон студентом.\n\n| ID | Цель | Статус | Факт |\n|---|---|---|---|\n"+table+"\n\n"+json.dumps(summary,ensure_ascii=False)+"\n")
    print(json.dumps(summary,ensure_ascii=False))
    assert totals["FAIL"]==0, "See original FAIL evidence before fixing or retesting."


if __name__=="__main__":
    main()
