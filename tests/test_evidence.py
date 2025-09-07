from pathlib import Path

from cyberzard.evidence import preserve_file

def test_preserve_file(tmp_path: Path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"hello")
    evidence_dir = tmp_path / "evidence"
    meta = preserve_file(f, evidence_dir)
    assert meta.get("sha256") is not None
    stored = Path(meta["stored_path"])
    assert stored.exists()
