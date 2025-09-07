import pathlib, re

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
LEGACY_PATTERN = re.compile(r"from\s+cyberzard|import\s+cyberzard")

EXEMPT_FILES = {
    'cyberzard/__init__.py',  # deprecation shim
    'cyberzard/MIGRATION.md',
}

def test_no_legacy_cyberzard_imports():
    offenders = []
    for path in PROJECT_ROOT.rglob('*'):
        if path.is_dir():
            continue
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        if rel in EXEMPT_FILES:
            continue
        # Only scan code / docs text
        if path.suffix not in {'.py', '.md', '.rst', '.txt'}:
            continue
        try:
            text = path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        if LEGACY_PATTERN.search(text):
            offenders.append(rel)
    assert not offenders, f"Legacy cyberzard imports found: {offenders}"
