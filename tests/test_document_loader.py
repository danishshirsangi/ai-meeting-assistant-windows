from core.document_loader import chunk_text, load_document


def test_load_text_document(tmp_path):
    path = tmp_path / "resume.txt"
    path.write_text("Python and SQL experience", encoding="utf-8")
    assert load_document(path) == "Python and SQL experience"


def test_chunk_text_empty_input():
    assert chunk_text("   \n  ") == []


def test_chunk_text_preserves_content():
    source = "A" * 400 + ". " + "B" * 400 + ". " + "C" * 400
    chunks = chunk_text(source, chunk_size=250, overlap=30)
    assert len(chunks) >= 2
    combined = " ".join(chunks)
    assert "A" * 100 in combined
    assert "B" * 100 in combined
    assert "C" * 100 in combined
