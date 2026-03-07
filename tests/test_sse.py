import pytest
import json
from unittest.mock import AsyncMock
from src.main import event_generator

@pytest.mark.asyncio
async def test_event_generator():
    mock_request = AsyncMock()
    mock_request.is_disconnected.return_value = False
    
    gen = event_generator(mock_request)
    
    # Extract the first yielded element
    event = await anext(gen)
    
    assert isinstance(event, dict)
    assert "data" in event
    
    payload = json.loads(event["data"])
    assert "desktops" in payload
    assert "windows" in payload
    assert "terminals" in payload
