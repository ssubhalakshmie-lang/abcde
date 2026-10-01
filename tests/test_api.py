from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_homepage_loads() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "EduGenie" in response.text


def test_ocean_question_works_in_demo_mode(monkeypatch) -> None:
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("AI_BASE_URL", raising=False)

    response = client.post(
        "/api/study",
        json={"action": "ask", "content": "Which is the largest ocean?"},
    )

    assert response.status_code == 200
    assert response.json()["mode"] == "demo"
    assert "Pacific Ocean" in response.json()["answer"]


def test_pythagorean_quiz_is_available_in_demo_mode(monkeypatch) -> None:
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("AI_BASE_URL", raising=False)

    response = client.post(
        "/api/study",
        json={"action": "quiz", "content": "The Pythagoras Theorem"},
    )

    assert response.status_code == 200
    assert "Answer key" in response.json()["answer"]
    assert "3 cm" in response.json()["answer"]


def test_sql_learning_path_is_available_in_demo_mode(monkeypatch) -> None:
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("AI_BASE_URL", raising=False)

    response = client.post(
        "/api/study",
        json={"action": "path", "content": "SQL"},
    )

    assert response.status_code == 200
    assert "Foundations" in response.json()["answer"]
    assert "weeks 7-8" in response.json()["answer"]


def test_summary_action_returns_response(monkeypatch) -> None:
    monkeypatch.delenv("AI_API_KEY", raising=False)
    monkeypatch.delenv("AI_BASE_URL", raising=False)

    response = client.post(
        "/api/study",
        json={
            "action": "summarize",
            "content": "Rivers carry water. They shape landscapes. Many support ecosystems.",
        },
    )

    assert response.status_code == 200
    assert "Key points" in response.json()["answer"]


def test_blank_content_is_rejected() -> None:
    response = client.post("/api/study", json={"action": "ask", "content": "   "})

    assert response.status_code == 422