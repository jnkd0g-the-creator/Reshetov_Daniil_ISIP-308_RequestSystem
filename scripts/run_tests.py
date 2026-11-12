"""One-command test run, complete output and machine-readable provenance."""

import json
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree

from test_environment import source_hash

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "testing/lab10"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, "-m", "pytest", "tests", "testing/lab10", "--cov=coffeedesk", "--cov-report=term-missing", "--cov-report=json:testing/lab10/coverage.json", "--cov-report=xml:testing/lab10/coverage.xml", "--junitxml=testing/lab10/junit.xml", "-v"]
    with (OUT / "test_run.txt").open("w", encoding="utf-8") as log:
        log.write("$ " + " ".join(command) + "\n")
        process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            print(line, end="", flush=True)
            log.write(line)
        process.wait()
    metadata = {"date": "2026-11-12", "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(), "source_sha256": source_hash(), "source_uncommitted": subprocess.run(["git", "diff", "--quiet", "HEAD", "--", "src"], cwd=ROOT).returncode != 0, "exit_code": process.returncode}
    if (OUT / "junit.xml").exists():
        suites = ElementTree.parse(OUT / "junit.xml").getroot().findall("testsuite")
        metadata.update({key: sum(int(s.attrib.get(key, 0)) for s in suites) for key in ["tests", "failures", "errors", "skipped"]})
    if (OUT / "coverage.json").exists():
        metadata["coverage_percent"] = json.loads((OUT / "coverage.json").read_text())["totals"]["percent_covered"]
    (OUT / "run_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    raise SystemExit(process.returncode)


if __name__ == "__main__":
    main()
