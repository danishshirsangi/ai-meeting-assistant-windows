from core.resume_rag import ResumeRAG


class FakeEmbeddingClient:
    def embed(self, texts, purpose="document", titles=None):
        return [
            [1.0, 0.0] if "Python" in text else [0.0, 1.0]
            for text in texts
        ]


def test_resume_rag_indexes_and_retrieves(tmp_path):
    resume = tmp_path / "resume.txt"
    resume.write_text(
        "Python engineer with SQL and data pipeline experience. "
        "Built ETL workflows and dashboards for operational reporting.",
        encoding="utf-8",
    )
    rag = ResumeRAG(FakeEmbeddingClient(), persist_dir=tmp_path / "index")
    count = rag.add_file(resume)

    assert count >= 1
    retrieved = rag.retrieve("Python")
    assert retrieved
    assert "Python" in retrieved[0]
