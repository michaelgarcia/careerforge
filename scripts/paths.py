"""Where CareerForge keeps things.

The repository is the product. Everything personal (career documents, the
knowledge base, preferences, postings, generated output, the jobs database)
lives under user_data/, which is gitignored and has no tracked files, so a
`git pull` never has anything there to change. user_data/ keeps the same
subfolder names: knowledge_base/, config/, postings/, output/, data/.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT / "templates"
USER_DATA = ROOT / "user_data"
