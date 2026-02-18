"""
update_progress.py
------------------
Run this after every Kaggle publish + before every git push.
Tracks:
  - How many notebooks published (based on a published/ subfolder or a published.txt log)
  - How many datasets published
  - Auto-updates README.md badges + Topics Covered table   ← FIXED
  - Writes PROGRESS.md
  - Writes CHANGELOG.md
"""

import re
from datetime import datetime, date
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent

# ── Category config ──────────────────────────────────────────────────────────
# Each entry:  (folder-name,  display-name,  planned-count)
CATEGORY_CONFIG = [
    ("computer-vision",    "Computer Vision",      30),
    ("machine-learning",   "Machine Learning",     30),
    ("deep-learning-gpu",  "Deep Learning (GPU)",  28),
    ("nlp",                "NLP",                  24),
    ("math-statistics",    "Math & Statistics",    24),
    ("eda-visualization",  "EDA & Visualization",  14),
]

CATEGORIES     = [c[0] for c in CATEGORY_CONFIG]
DISPLAY_NAMES  = {c[0]: c[1] for c in CATEGORY_CONFIG}
PLANNED_COUNTS = {c[0]: c[2] for c in CATEGORY_CONFIG}

DATASET_FOLDERS = [
    "datasets/image-datasets",
    "datasets/tabular-datasets",
    "datasets/nlp-datasets",
    "datasets/time-series-datasets",
    "datasets/competition-ready-datasets",
]

TARGET_NOTEBOOKS = 150
TARGET_DATASETS  = 30


# ── Counting helpers ─────────────────────────────────────────────────────────

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


# ── README updaters ───────────────────────────────────────────────────────────

def update_badges(content: str, notebooks_done: int, datasets_done: int) -> str:
    """Update the two shield.io badge counts in the README."""
    content = re.sub(
        r"Notebooks%20Published-\d+%20%2F%20\d+",
        f"Notebooks%20Published-{notebooks_done}%20%2F%20{TARGET_NOTEBOOKS}",
        content,
    )
    content = re.sub(
        r"Datasets%20Published-\d+%20%2F%20\d+",
        f"Datasets%20Published-{datasets_done}%20%2F%20{TARGET_DATASETS}",
        content,
    )
    return content


def update_topics_table(content: str, nb_published: dict) -> str:
    """
    Rewrite the Topics Covered table rows with live published counts.

    Looks for the markdown table that contains the header line:
        | Category | Notebooks | Published |
    and replaces every data row + the Total row.
    """
    total_planned   = sum(PLANNED_COUNTS.values())
    total_published = sum(nb_published.values())

    # Build the replacement body rows
    data_rows = []
    for cat in CATEGORIES:
        display  = DISPLAY_NAMES[cat]
        planned  = PLANNED_COUNTS[cat]
        pub      = nb_published.get(cat, 0)
        data_rows.append(f"| {display} | {planned} | {pub} |")
    data_rows.append(f"| **Total** | **{total_planned}** | **{total_published}** |")

    new_rows_block = "\n".join(data_rows)

    # Regex: match the header + separator + all following pipe-rows of this table
    pattern = re.compile(
        r"(\| Category \| Notebooks \| Published \|\s*\n"   # header row
        r"\|[-| ]+\|\s*\n)"                                  # separator row
        r"(?:\|.*\|\s*\n?)+",                                # all data rows
        re.IGNORECASE,
    )

    def replacer(m):
        return m.group(1) + new_rows_block + "\n"

    updated, n = pattern.subn(replacer, content)
    if n == 0:
        print("  [warn] Topics Covered table not found — check README formatting")
    return updated


def update_published_count_line(content: str, notebooks_done: int) -> str:
    """Update the 'Published: N' line in the About section."""
    return re.sub(
        r"(\*\*Published:\*\*\s*)\d+",
        rf"\g<1>{notebooks_done}",
        content,
    )


def update_readme(nb_published: dict, datasets_done: int):
    path = BASE / "README.md"
    if not path.exists():
        print("  [skip] README.md not found")
        return

    notebooks_done = sum(nb_published.values())
    content = path.read_text(encoding="utf-8")
    original = content

    content = update_badges(content, notebooks_done, datasets_done)
    content = update_topics_table(content, nb_published)
    content = update_published_count_line(content, notebooks_done)

    if content != original:
        path.write_text(content, encoding="utf-8")
        print(f"  [updated] README.md -> {notebooks_done} notebooks / {datasets_done} datasets")
    else:
        print("  [no change] README.md already up to date")


# ── PROGRESS.md ───────────────────────────────────────────────────────────────

def write_progress_md(nb_by_cat: dict, notebooks_done: int, datasets_done: int):
    today = date.today().strftime("%B %d, %Y")
    lines = [
        "# Progress Log\n",
        f"Last updated: {today}\n",
        "",
        "## Summary\n",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Notebooks Published | {notebooks_done} / {TARGET_NOTEBOOKS} |",
        f"| Datasets Published  | {datasets_done} / {TARGET_DATASETS} |",
        "",
        "## By Category\n",
        "| Category | Planned | Published |",
        "|----------|---------|-----------|",
    ]
    for cat in CATEGORIES:
        display = DISPLAY_NAMES[cat]
        planned = PLANNED_COUNTS[cat]
        pub     = nb_by_cat.get(cat, 0)
        lines.append(f"| {display} | {planned} | {pub} |")
    lines.append("")
    (BASE / "PROGRESS.md").write_text("\n".join(lines), encoding="utf-8")
    print("  [done] PROGRESS.md")


# ── CHANGELOG.md ──────────────────────────────────────────────────────────────

def write_changelog_md():
    lines = [
        "# Changelog\n",
        "Track every notebook and dataset published to Kaggle.\n",
        "",
        "## How to add an entry\n",
        "Entries are auto-added via commit messages starting with `[publish]` or `[dataset]`.\n",
        "Run this script after every push to keep it updated.\n",
    ]
    (BASE / "CHANGELOG.md").write_text("\n".join(lines), encoding="utf-8")
    print("  [done] CHANGELOG.md")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("\n=== update_progress.py ===\n")

    nb_published   = count_notebooks("published")
    nb_planned     = count_notebooks("all")
    ds_published   = count_datasets("published")
    notebooks_done = sum(nb_published.values())

    for cat in CATEGORIES:
        pub     = nb_published.get(cat, 0)
        planned = nb_planned.get(cat, 0)
        display = DISPLAY_NAMES[cat]
        print(f"  {display:<25}  {pub} published / {planned} planned")

    print(f"\n  Notebooks published : {notebooks_done} / {TARGET_NOTEBOOKS}")
    print(f"  Datasets published  : {ds_published} / {TARGET_DATASETS}\n")

    print("Updating README.md ...")
    update_readme(nb_published, ds_published)

    print("Writing PROGRESS.md ...")
    write_progress_md(nb_published, notebooks_done, ds_published)

    print("Writing CHANGELOG.md ...")
    write_changelog_md()

    print("\nAll done. Now run:\n")
    print("  git add .")
    print('  git commit -m "[publish] category/difficulty/notebook-name"')
    print("  git push origin main\n")


if __name__ == "__main__":
    main()
