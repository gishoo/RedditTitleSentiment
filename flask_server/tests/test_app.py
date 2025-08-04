import pytest
from app import app, db, URLTitle
from unittest.mock import patch


@pytest.fixture
def client():
    # Use an in-memory SQLite DB for testing
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()


@patch("app.extract_reddit_title", return_value="Mock Reddit Title")
@patch("app.call_external_api", return_value="Good")
def test_analyze_new_url(mock_call_api, mock_extract, client):
    response = client.post("/analyze", data={"url": "https://reddit.com/r/test"})
    assert response.status_code == 200
    assert b"Mock Reddit Title" in response.data
    assert b"Good" in response.data


@patch("app.extract_reddit_title", return_value="Mock Reddit Title")
@patch("app.call_external_api", return_value="Neutral")
def test_analyze_existing_url(mock_call_api, mock_extract, client):
    # Add entry to DB
    with app.app_context():
        entry = URLTitle(url="https://reddit.com/r/test", title="Cached Title")
        db.session.add(entry)
        db.session.commit()

    response = client.post("/analyze", data={"url": "https://reddit.com/r/test"})
    assert response.status_code == 200
    assert b"Cached Title" in response.data
    mock_extract.assert_not_called()  # Should use cached title


def test_history_empty(client):
    response = client.get("/history")
    assert response.status_code == 200
    assert b"Stored URL Titles" in response.data


@patch("app.extract_reddit_title", return_value="Updated Title")
@patch("app.call_external_api", return_value="Bad")
def test_reanalyze_updates_title(mock_call_api, mock_extract, client):
    # Add entry
    with app.app_context():
        entry = URLTitle(url="https://reddit.com/r/test", title="Old Title")
        db.session.add(entry)
        db.session.commit()

    response = client.post("/reanalyze", data={"url": "https://reddit.com/r/test"})
    assert response.status_code == 200
    assert b"Updated Title" in response.data
    assert b"Bad" in response.data
