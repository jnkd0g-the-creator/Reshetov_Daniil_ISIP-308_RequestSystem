"""Real conflict in an isolated sandbox; never rewrites project history."""

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    (ROOT / ".local").mkdir(exist_ok=True)
    sandbox = Path(tempfile.mkdtemp(prefix="git-conflict-", dir=ROOT / ".local"))
    output = []

    def git(*args, expected=0):
        result = subprocess.run(["git", *args], cwd=sandbox, capture_output=True, text=True)
        output.append("$ git " + " ".join(args) + "\n" + result.stdout + result.stderr)
        assert result.returncode == expected, output[-1]

    git("init", "-b", "main")
    git("config", "user.name", "Training Demo")
    git("config", "user.email", "training@example.invalid")
    path = sandbox / "README.md"
    path.write_text("CoffeeDesk: requests.\n")
    git("add", "README.md")
    git("commit", "-m", "initial")
    git("switch", "-c", "develop")
    path.write_text("CoffeeDesk: coffee-bar maintenance requests.\n")
    git("commit", "-am", "clarify domain")
    git("switch", "main")
    path.write_text("CoffeeDesk: register and track requests.\n")
    git("commit", "-am", "clarify purpose")
    git("merge", "develop", expected=1)
    git("status", "--short")
    git("diff")
    path.write_text("CoffeeDesk: register and track coffee-bar maintenance requests.\n")
    git("add", "README.md")
    git("commit", "-m", "resolve: preserve purpose and domain")
    git("status", "--short")
    git("log", "--graph", "--oneline", "--all")
    target = ROOT / "docs/evidence/git_conflict.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(output), encoding="utf-8")
    print(target.relative_to(ROOT))


if __name__ == "__main__":
    main()
