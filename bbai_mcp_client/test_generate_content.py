import pytest
from fastapi.testclient import TestClient
from generate_content import app
import os

client = TestClient(app)

def test_generate_content_mock():
    # Set mock mode
    os.environ["MOCK_MCP"] = "true"
    response = client.post("/generate-content", json={
        "repository": "test/repo",
        "event": "push",
        "commit_sha": "abc123",
        "branch": "main"
    })
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "content" in data
    assert "Content generated (mock mode)" in data["message"]

def test_generate_content_invalid_event():
    os.environ["MOCK_MCP"] = "true"
    response = client.post("/generate-content", json={
        "repository": "test/repo",
        "event": "invalid",
        "commit_sha": "abc123",
        "branch": "main"
    })
    assert response.status_code == 200  # Since it still generates, but could be improved

def test_generate_content_missing_field():
    os.environ["MOCK_MCP"] = "true"
    response = client.post("/generate-content", json={
        "repository": "test/repo",
        "event": "push",
        "commit_sha": "abc123"
        # missing branch
    })
    assert response.status_code == 422  # Validation error

if __name__ == "__main__":
    pytest.main([__file__])
