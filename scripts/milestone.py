"""Publish explicitly selected milestone files; never force-push or rewrite."""

import argparse
import subprocess

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("message")
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()
    subprocess.run(["git", "add", "--", *args.files], check=True)
    subprocess.run(["git", "diff", "--cached", "--check"], check=True)
    subprocess.run(["git", "commit", "-m", args.message], check=True)
    branch = subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()
    subprocess.run(["git", "push", "-u", "origin", branch], check=True)
