"""Keep GitHub-relative source/evidence links usable in a non-deployed docs build.

Only transforms links to existing files/directories inside this repository which
are intentionally outside the generated site's input set. Does not read archive
contents, execute templates, fetch URLs or change Markdown source files.
"""
from pathlib import Path
import re
from urllib.parse import quote, unquote, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
REPO = "https://github.com/Apdelrahman1911/nativeCmpkit"
EXCLUDED_PREFIXES = ("migration/upstream-metadata/", "migration/git/", "migration/legacy/", "testing/evidence/", "testing/native-features-probes/", "audit/issue-drafts/", "audit/findings/")
EXCLUDED_FILES = {"audit/source-inventory.json"}


def repository_link(url, page_path, root=ROOT):
    parts = urlsplit(url)
    if parts.scheme or parts.netloc or not parts.path or parts.path.startswith("/"):
        return url
    docs = root / "docs"
    target = (docs / page_path).parent / unquote(parts.path)
    target = target.resolve()
    if not target.is_relative_to(root.resolve()) or not target.exists():
        return url
    if target.is_relative_to(docs.resolve()):
        rel = target.relative_to(docs.resolve()).as_posix()
        excluded = rel in EXCLUDED_FILES or any((rel + "/").startswith(p) for p in EXCLUDED_PREFIXES)
        if not excluded and not target.is_dir():
            return url
    path = target.relative_to(root.resolve()).as_posix()
    return urlunsplit(("https", "github.com", "/Apdelrahman1911/nativeCmpkit/" + ("tree" if target.is_dir() else "blob") + "/main/" + quote(path, safe="/"), parts.query, parts.fragment))


def on_page_markdown(markdown, page, config, files):
    return re.sub(r"(\]\()([^\s)]+)(\))", lambda m: m[1] + repository_link(m[2], page.file.src_uri) + m[3], markdown)
