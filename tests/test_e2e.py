import pytest
import httpx
import json

BASE_URL = "http://localhost:8000/api/v1"

@pytest.mark.asyncio
async def test_dashboard_endpoint():
    """Verify that the dashboard endpoint returns structured data and score breakdowns."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/data/dashboard")
        assert response.status_code == 200, "Dashboard endpoint should return 200 OK"
        
        data = response.json()
        assert "opportunities" in data, "Dashboard response missing opportunities"
        
        # Verify opportunity structure
        if len(data["opportunities"]) > 0:
            first_opp = data["opportunities"][0]
            assert "title" in first_opp
            assert "description" in first_opp
            assert "reach_score" in first_opp
            assert "user_pain" in first_opp
            assert "business_impact" in first_opp
            assert "evidence_strength" in first_opp

@pytest.mark.asyncio
async def test_chat_streaming_endpoint():
    """Verify that the RAG chat streaming endpoint works and returns chunks."""
    async with httpx.AsyncClient() as client:
        payload = {
            "messages": [
                {"role": "user", "content": "What are the common failure modes for face grouping in Google Photos?"}
            ],
            "stream": True
        }
        
        # We test with stream=True because it's the primary way the UI consumes this
        async with client.stream("POST", f"{BASE_URL}/chat", json=payload) as response:
            assert response.status_code == 200, "Chat endpoint should return 200 OK"
            
            # Read first few chunks to verify SSE format
            chunk_count = 0
            async for chunk in response.aiter_lines():
                if chunk.startswith("data: "):
                    data_str = chunk.replace("data: ", "")
                    if data_str == "[DONE]":
                        break
                    
                    data = json.loads(data_str)
                    assert "content" in data or "citations" in data
                    chunk_count += 1
                    
                    if chunk_count > 5:
                        break # Only need to verify stream works
            
            assert chunk_count > 0, "No chunks returned from RAG streaming endpoint"
