from pathlib import Path
import os
import re

root = Path(r"c:\Users\HP\Desktop\OpenJarvis-main")

# Rename paths that explicitly contain the old project name.
renames = [
    (root / "src" / "openjarvis", root / "src" / "friday"),
    (root / "configs" / "openjarvis", root / "configs" / "friday"),
    (root / "deploy" / "launchd" / "com.openjarvis.plist", root / "deploy" / "launchd" / "com.friday.plist"),
    (root / "deploy" / "systemd" / "openjarvis.service", root / "deploy" / "systemd" / "friday.service"),
]
for src, dst in renames:
    if src.exists() and not dst.exists():
        src.rename(dst)

# Replace branding across text files.
replacements = [
    ("OpenJarvis", "Friday"),
    ("openjarvis", "friday"),
    ("Jarvis", "Friday"),
    ("jarvis", "friday"),
    ("https://github.com/open-jarvis/OpenJarvis", "https://github.com/purnasai1807-lgtm/Friday_AI"),
    ("https://open-jarvis.github.io/OpenJarvis", "https://purnasai1807-lgtm.github.io/Friday_AI"),
]

text_exts = {
    '.md', '.toml', '.yaml', '.yml', '.json', '.py', '.pyi', '.rs', '.ts', '.tsx', '.js', '.jsx', '.sh', '.ps1', '.txt', '.html', '.css', '.xml', '.cfg', '.ini', '.cfg', '.service', '.plist', '.sql', '.lock'
}

for path in root.rglob('*'):
    if not path.is_file():
        continue
    if path.name in {'.DS_Store', 'tmp_rename_project.py'}:
        continue
    if path.suffix.lower() in {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico', '.pdf', '.zip', '.gz', '.tar', '.whl', '.so', '.dll', '.pyd', '.pyc', '.db', '.sqlite3'}:
        continue
    try:
        text = path.read_text(encoding='utf-8')
    except Exception:
        continue
    new_text = text
    for old, new in replacements:
        new_text = new_text.replace(old, new)
    if new_text != text:
        path.write_text(new_text, encoding='utf-8')

print('branding rename completed')
