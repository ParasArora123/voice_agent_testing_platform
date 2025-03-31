from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class CallState:
    id: str # Primary key, must be unique
    vonage_uuid: str
    agent_id: str  # Foreign key to the Agents table that represents the test agent associated with this call
    transcript: Optional[str] = None  # Transcript of the call
    max_duration_sec: int = 300  # Maximum duration of the call in seconds
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()