"""Check artefacts and scan actual local demo credentials without printing them."""

import csv
import json
import sqlite3
import subprocess
from pathlib import Path
from zipfile import ZipFile

from docx import Document

ROOT = Path(__file__).resolve().parents[1]


def main():
    records=[]
    reports=sorted((ROOT/"docs/reports").glob("Lab_*.docx"))
    assert len(reports)==10
    for path in reports:
        with ZipFile(path) as archive:
            assert archive.testzip() is None
            assert "word/document.xml" in archive.namelist()
        doc=Document(path)
        assert len(doc.paragraphs)>15 and len(doc.inline_shapes)>=1
        records.append(f"{path.name}: valid DOCX, {len(doc.paragraphs)} paragraphs, {len(doc.inline_shapes)} project images")
    with (ROOT/"testing/lab9/test_cases.csv").open(encoding="utf-8-sig",newline="") as file:
        cases=list(csv.DictReader(file,delimiter=";"))
    assert len(cases)>=20 and all(row["status"]=="PASS" for row in cases)
    assert all(row["manual_status"]=="BLOCKED" for row in cases)
    with sqlite3.connect(ROOT/"docs/database/coffee_demo.sqlite3") as con:
        assert con.execute("SELECT COUNT(*) FROM Requests").fetchone()[0]==12
        assert con.execute("SELECT COUNT(*) FROM Users WHERE password_hash<>'!unset'").fetchone()[0]==0
        assert con.execute("SELECT COUNT(*) FROM Sessions").fetchone()[0]==0
    private_values=[]
    for name in ["demo_credentials.txt","docker_credentials.txt"]:
        path=ROOT/".local"/name
        if path.exists():
            private_values.extend(line.split("\t",1)[1].encode() for line in path.read_text().splitlines() if "\t" in line)
    names=subprocess.check_output(["git","ls-files","--cached","--others","--exclude-standard","-z"],cwd=ROOT).decode().split("\0")
    checked=0
    for name in filter(None,names):
        assert not name.startswith((".local/",".venv/","data/")) and name!=".env", f"Private file selected for Git: {name}"
        path=ROOT/name
        if not path.is_file():
            continue
        payload=path.read_bytes()
        if path.suffix==".docx":
            with ZipFile(path) as archive:
                payload+=b"".join(archive.read(entry) for entry in archive.namelist() if entry.endswith(".xml"))
        assert not any(value in payload for value in private_values), f"Local credential found in {name}"
        checked+=1
    records.extend([f"{len(cases)} executed cases PASS; {len(cases)} student manual reviews honestly BLOCKED", "Public SQLite: 12 requests, !unset passwords, zero sessions",f"{checked} versioned/candidate files scanned: no actual local demo passwords, private dirs or .env", "This targeted scan is not a general-purpose security audit."])
    result={"result":"PASS","checks":records,"known_external_blocks":["remote deployment","student manual review","student voiced final video"]}
    (ROOT/"docs/delivery_validation.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("Deliverable validation PASS; private credential values never printed.")


if __name__=="__main__":
    main()
