from pathlib import Path

root = Path(r"C:/Users/HP/Desktop/OpenFriday AI-main")
replacements = [
    ("https://github.com/purnasai1807-lgtm/Friday_AI", "https://github.com/purnasai1807-lgtm/Friday_AI"),
    ("https://github.com/purnasai1807-lgtm/Friday_AI.git", "https://github.com/purnasai1807-lgtm/Friday_AI.git"),
    ("https://github.com/purnasai1807-lgtm/Friday_AI/issues", "https://github.com/purnasai1807-lgtm/Friday_AI/issues"),
    ("https://github.com/purnasai1807-lgtm/Friday_AI/discussions", "https://github.com/purnasai1807-lgtm/Friday_AI/discussions"),
    ("https://github.com/purnasai1807-lgtm/Friday_AI/releases", "https://github.com/purnasai1807-lgtm/Friday_AI/releases"),
    ("https://purnasai1807-lgtm.github.io/Friday_AI/", "https://purnasai1807-lgtm.github.io/Friday_AI/"),
    ("purnasai1807-lgtm/Friday_AI", "purnasai1807-lgtm/Friday_AI"),
    ("Purnasai AVVARU", "Purnasai AVVARU"),
    ("Purnasai AVVARU", "Purnasai AVVARU"),
    ("Purnasai AVVARU", "Purnasai AVVARU"),
    ("purnasai1807-lgtm", "purnasai1807-lgtm"),
    ("purna-sai-avvaru-803868377", "purna-sai-avvaru-803868377"),
    ("purnasai1807-lgtm", "purnasai1807-lgtm"),
    ("Friday AI", "Friday AI"),
    ("Friday AI", "Friday AI"),
    ("Friday AI", "Friday AI"),
    ("https://www.linkedin.com/in/purna-sai-avvaru-803868377-/", "https://www.linkedin.com/in/purna-sai-avvaru-803868377/"),
    ("https://www.linkedin.com/in/purna-sai-avvaru-803868377-", "https://www.linkedin.com/in/purna-sai-avvaru-803868377/"),
    ("https://github.com/purnasai1807-lgtm", "https://github.com/purnasai1807-lgtm"),
    ("https://x.com/purnasai1807-lgtm", "https://github.com/purnasai1807-lgtm"),
]
text_exts = {'.md', '.toml', '.yaml', '.yml', '.json', '.py', '.pyi', '.rs', '.ts', '.tsx', '.js', '.jsx', '.sh', '.ps1', '.txt', '.html', '.css', '.xml', '.cfg', '.ini', '.service', '.plist', '.sql', '.lock'}
exclude_dirs = {'.git', 'node_modules', '__pycache__', 'site', 'dist', 'build', '.venv', 'venv', 'env', 'myenv', '.pytest_cache', '.ruff_cache', 'target', '.idea', '.vscode'}
exclude_files = {'.DS_Store', 'tmp_rename_project.py'}
changed = 0
for path in root.rglob('*'):
    if not path.is_file():
        continue
    if any(part in exclude_dirs for part in path.parts):
        continue
    if path.name in exclude_files:
        continue
    if path.suffix.lower() not in text_exts:
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
        changed += 1
print(changed)
