from locust import HttpUser, task, between
import json

class DiscoveryEngineUser(HttpUser):
    # Simulate a PM thinking between actions for 1-5 seconds
    wait_time = between(1, 5)

    @task(3)
    def view_dashboard(self):
        """Simulate a PM loading the dashboard (frequent action)."""
        self.client.get("/api/v1/data/dashboard", name="Load Dashboard")

    @task(1)
    def query_assistant(self):
        """Simulate a PM querying the UX research assistant."""
        payload = {
            "messages": [
                {"role": "user", "content": "What are the common failure modes for face grouping in Google Photos?"}
            ],
            "stream": False # Use false for load testing to easily measure full response time
        }
        
        # We use a POST request to the chat endpoint
        with self.client.post("/api/v1/chat", json=payload, name="Query RAG Assistant", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "content" in data or "choices" in data:
                        response.success()
                    else:
                        response.failure("Response missing expected content structure")
                except json.JSONDecodeError:
                    response.failure("Failed to decode JSON response")
            else:
                response.failure(f"Expected 200 OK, got {response.status_code}")
