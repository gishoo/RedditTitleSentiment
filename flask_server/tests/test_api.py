import pytest
from api import app
from unittest.mock import patch


@pytest.fixture
def client():
    app.config['TESTING'] = True
    return app.test_client()


@patch("api.tokenizer")
@patch("api.model")
def test_analyze_local_model(mock_model, mock_tokenizer, client):
    # Mock tokenizer output
    mock_tokenizer.return_value = {"input_ids": [], "attention_mask": []}
    # Mock model output
    class MockOutputs:
        logits = [[0.1, 0.2, 0.7]]
    mock_model.__call__ = lambda *a, **kw: MockOutputs()

    response = client.post("/analyze", json={"title": "This is great"})
    assert response.status_code == 200
    data = response.get_json()
    assert "sentiment" in data
    assert data["sentiment"] in ["positive", "neutral", "negative"]


def test_analyze_missing_title(client):
    response = client.post("/analyze", json={})
    assert response.status_code == 400
    assert "error" in response.get_json()


@patch("api.sentiment_pipeline", return_value=[{"label": "POSITIVE", "score": 0.9}])
def test_analyze_huggingface_pipeline(mock_pipeline, client):
    # Force huggingface mode
    from api import mode
    import api
    api.mode = "huggingface"
    response = client.post("/analyze", json={"title": "Awesome!"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["sentiment"] == "positive"
