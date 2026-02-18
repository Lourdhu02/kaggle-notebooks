"""
update_progress.py
------------------
Run this after every Kaggle publish + before every git push.
Tracks:
  - How many notebooks published (based on a published/ subfolder or a published.txt log)
  - How many datasets published
  - Auto-updates README.md badges
  - Writes PROGRESS.md
  - Writes CHANGELOG.md
"""

import re
from datetime import datetime, date
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent

CATEGORIES = [
    "computer-vision",
    "machine-learning",
    "deep-learning-gpu",
    "nlp",
    "math-statistics",
    "eda-visualization",
]

DATASET_FOLDERS = [
    "datasets/image-datasets",
    "datasets/tabular-datasets",
    "datasets/nlp-datasets",
    "datasets/time-series-datasets",
    "datasets/competition-ready-datasets",
]

TARGET_NOTEBOOKS = 150
TARGET_DATASETS  = 30


def count_notebooks(status: str = "all") -> dict:
    """
    Count .ipynb files per category.
    status = "all"       -> count everything (planned)
    status = "published" -> count only files inside a published/ subfolder
    """
    result = {}
    for cat in CATEGORIES:
        cat_path = BASE / cat
        if not cat_path.exists():
            result[cat] = 0
            continue
        if status == "published":
            result[cat] = len(list(cat_path.rglob("published/*.ipynb")))
        else:
            result[cat] = len(list(cat_path.rglob("*.ipynb")))
    return result


def count_datasets(status: str = "published") -> int:
    total = 0
    for folder in DATASET_FOLDERS:
        path = BASE / folder
        if status == "published":
            total += len(list((path / "published").rglob("*.*"))) if (path / "published").exists() else 0
        else:
            total += len([f for f in path.glob("*.*") if f.suffix != ""])
    return total


def update_readme(notebooks_done: int, datasets_done: int):
    path = BASE / "README.md"
    if not path.exists():
        return
    content = path.read_text(encoding="utf-8")

    updated = re.sub(
        r"Notebooks%20Published-\d+%20%2F%20\d+",
        f"Notebooks%20Published-{notebooks_done}%20%2F%20{TARGET_NOTEBOOKS}",
        content
    )
    updated = re.sub(
        r"Datasets%20Published-\d+%20%2F%20\d+",
        f"Datasets%20Published-{datasets_done}%20%2F%20{TARGET_DATASETS}",
        updated
    )

    if updated != content:
        path.write_text(updated, encoding="utf-8")
        print(f"  [updated] README.md -> {notebooks_done} notebooks / {datasets_done} datasets")
    else:
        print("  [no change] README.md already up to date")


def write_progress_md(nb_by_cat: dict, notebooks_done: int, datasets_done: int):
    today = date.today().strftime("%B %d, %Y")
    lines = []
    lines.append("# Progress Log\n")
    lines.append(f"Last updated: {today}\n")
    lines.append("")
    lines.append("## Summary\n")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Notebooks Published | {notebooks_done} / {TARGET_NOTEBOOKS} |")
    lines.append(f"| Datasets Published  | {datasets_done} / {TARGET_DATASETS} |")
    lines.append("")
    lines.append("## By Category\n")
    lines.append("| Category | Published |")
    lines.append("|----------|-----------|")
    for cat, count in nb_by_cat.items():
        lines.append(f"| {cat} | {count} |")
    lines.append("")
    (BASE / "PROGRESS.md").write_text("\n".join(lines), encoding="utf-8")
    print("  [done] PROGRESS.md")


def write_changelog_md():
    """Read git log for [publish] commits and format as changelog."""
    lines = []
    lines.append("# Changelog\n")
    lines.append("Track every notebook and dataset published to Kaggle.\n")
    lines.append("")
    lines.append("## How to add an entry\n")
    lines.append("Entries are auto-added via commit messages starting with `[publish]` or `[dataset]`.\n")
    lines.append("Run this script after every push to keep it updated.\n")
    (BASE / "CHANGELOG.md").write_text("\n".join(lines), encoding="utf-8")
    print("  [done] CHANGELOG.md")


def main():
    print("\n=== update_progress.py ===\n")

    nb_published  = count_notebooks("published")
    ds_published  = count_datasets("published")
    notebooks_done = sum(nb_published.values())

    for cat, count in nb_published.items():
        planned = count_notebooks("all").get(cat, 0)
        print(f"  {cat:<30}  {count} published / {planned} planned")

    print(f"\n  Notebooks published : {notebooks_done} / {TARGET_NOTEBOOKS}")
    print(f"  Datasets published  : {ds_published} / {TARGET_DATASETS}\n")

    print("Updating README.md ...")
    update_readme(notebooks_done, ds_published)

    print("Writing PROGRESS.md ...")
    write_progress_md(nb_published, notebooks_done, ds_published)

    print("Writing CHANGELOG.md ...")
    write_changelog_md()

    print("\nAll done. Now run:\n")
    print("  git add .")
    print("  git commit -m \"[publish] category/difficulty/notebook-name\"")
    print("  git push origin main\n")


if __name__ == "__main__":
    main()
