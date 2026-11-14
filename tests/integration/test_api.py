"""Integration tests for API endpoints."""

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_root(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data

    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "dependencies" in data

    def test_readiness(self):
        """Test readiness probe."""
        response = client.get("/api/v1/health/readiness")
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True

    def test_liveness(self):
        """Test liveness probe."""
        response = client.get("/api/v1/health/liveness")
        assert response.status_code == 200
        data = response.json()
        assert data["alive"] is True


class TestQueryEndpoints:
    """Tests for query endpoints."""

    def test_query_endpoint(self):
        """Test query endpoint."""
        request_data = {
            "query": "What is machine learning?",
            "top_k": 3,
            "use_reflection": False,
        }
        response = client.post("/api/v1/query", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "query" in data


class TestIngestEndpoints:
    """Tests for ingestion endpoints."""

    def test_ingest_text(self):
        """Test text ingestion endpoint."""
        request_data = {
            "text": "This is a test document for ingestion.",
            "metadata": {"source": "test", "type": "text"},
        }
        response = client.post("/api/v1/ingest", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert data.get("num_chunks") >= 1
