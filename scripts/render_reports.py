"""Optional LibreOffice rendering checks in isolated container (DOCX stays deliverable)."""

import json
import os
import subprocess
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT / ".local/reports_pdf"
    output.mkdir(parents=True, exist_ok=True)
    subprocess.run(["docker","build","-f","scripts/Dockerfile.reports","-t","coffeedesk-reports:local","."],cwd=ROOT,check=True)
    subprocess.run(["docker","run","--rm","--network","none","--user",f"{os.getuid()}:{os.getgid()}","--cap-drop","ALL","--security-opt","no-new-privileges:true","-v",str(ROOT/"docs/reports")+":/in:ro","-v",str(output)+":/out","coffeedesk-reports:local"],check=True)
    records=[]
    for path in sorted(output.glob("*.pdf")):
        reader=PdfReader(path)
        records.append({"report":path.stem+".docx","pages":len(reader.pages),"page_text_lengths":[len(page.extract_text() or "") for page in reader.pages]})
    first=next(record for record in records if record["report"].startswith("Lab_01"))
    assert 5<=first["pages"]<=7, f"Lab 1 must have 5–7 pages, got {first['pages']}"
    (ROOT/"docs/reports/render_validation.json").write_text(json.dumps({"renderer":"LibreOffice Writer 7.4, DejaVu fonts, offline container", "lab1_page_requirement":"PASS", "reports":records},ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(records,ensure_ascii=False))


if __name__=="__main__":
    main()
