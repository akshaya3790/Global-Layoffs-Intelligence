"""Build the `public-release` branch: one parentless commit made from main's tree minus every file that contains
rows from the technology layoffs file (unknown licence), with notebook 01-04 outputs cleared and this machine's
project folder path removed. It uses a temporary git index, so the working tree and branch `main` are never touched.

Usage (from the project root):
    python src/make_public_release.py

See PUBLIC_RELEASE.md for what is excluded and why. Nothing is pushed; publishing is a separate, manual step.
"""
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EXCLUDE = [r"^data/interim/", r"^data/processed/", r"^data/raw/tech_layoffs_2025_2026\.csv$",
           r"^reports/audit/history/.*/(tech_layoffs_staged|possible_duplicate_pairs|excluded_candidate_pairs)\.csv$",
           r"^reports/eda/03_T", r"^reports/figures/03_T", r"^reports/phase4/query_results/1[1-4]_",
           # historical reports that quote individual tech rows
           r"^reports/(history/)?PHASE1_VERIFICATION_REPORT.*\.md$", r"^reports/(history/)?PHASE2_APPROVAL_CHECKLIST\.md$",
           r"^reports/(history/)?PHASE2_CANONICAL_MODEL_PLAN\.md$", r"^reports/(history/)?PROJECT_STATUS_SUMMARY\.md$",
           r"^reports/(history/)?WORK_REPORT_2026-10-23_phase2_build\.md$",
           # page 4 images, the PDF and the .pbix show or embed the 35 tech rows
           r"^deliverables/validation/", r"^deliverables/screenshots/page4\.png$", r"^deliverables/.*\.(pbix|pdf)$"]
STRIP = r"^(notebooks/0[1-4]_.*|reports/audit/history/.*)\.ipynb$"      # outputs print tech rows; code is kept
TMDL = "powerbi/LayoffsDashboard.SemanticModel/definition/expressions.tmdl"
PLACEHOLDER = r"C:\path\to\Global-Layoffs-Intelligence"
LOCAL = str(REPO)
LOCAL_FORMS = [LOCAL.encode(), LOCAL.replace("\\", "\\\\").encode()]   # plain, and JSON-escaped in notebooks


def git(*args, inp=None, env=None):
    return subprocess.run(["git", *args], cwd=REPO, input=inp, capture_output=True, check=True,
                          env={**os.environ, **(env or {})}).stdout


def blob(data: bytes) -> str:
    return git("hash-object", "-w", "--stdin", inp=data).decode().strip()


def main():
    idx = os.path.join(tempfile.mkdtemp(), "index")
    env = {"GIT_INDEX_FILE": idx}
    git("read-tree", "main", env=env)
    removed, stripped = [], []
    for line in git("ls-files", "-s", env=env).decode().splitlines():
        meta, path = line.split("\t", 1)
        mode, sha = meta.split()[0], meta.split()[1]
        if any(re.search(p, path) for p in EXCLUDE):
            git("rm", "--cached", "-q", path, env=env)
            removed.append(path)
            continue
        new = None
        content = git("cat-file", "blob", sha)
        if re.search(STRIP, path):
            nb = json.loads(content)
            for c in nb["cells"]:
                if c["cell_type"] == "code":
                    c["outputs"], c["execution_count"] = [], None
            new = (json.dumps(nb, indent=1, ensure_ascii=False) + "\n").encode()
            stripped.append(path)
        elif path == TMDL:
            new = re.sub(rb'(expression ProjectFolder = ")[^"]*(")',
                         lambda m: m.group(1) + PLACEHOLDER.encode() + m.group(2), content)
        if path.endswith((".md", ".ipynb", ".csv", ".txt", ".json", ".py")):
            text = new if new is not None else content
            for local in LOCAL_FORMS:
                text = text.replace(local, b"<project folder>")
            if text != content:
                new = text
        if new is not None:
            git("update-index", "--cacheinfo", f"{mode},{blob(new)},{path}", env=env)
    tree = git("write-tree", env=env).decode().strip()
    msg = ("Public release of Global Layoffs Intelligence\n\n"
           "Built from main without data derived from the technology layoffs file, whose source and licence are "
           "unknown. See PUBLIC_RELEASE.md.\n\nCo-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>\n")
    commit = git("commit-tree", tree, inp=msg.encode()).decode().strip()
    git("update-ref", "refs/heads/public-release", commit)
    print("public-release ->", commit[:7], "| removed", len(removed), "| notebook outputs cleared", len(stripped))
    print("\n".join("  - " + r for r in removed))


if __name__ == "__main__":
    main()
