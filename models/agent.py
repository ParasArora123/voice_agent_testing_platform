from dataclasses import dataclass

@dataclass
class Agent:
    id: str # Primary key, must be unique
    name: str
    system_prompt: str
    llm_model_id: str
    tts_model_id: str
    stt_model_id: str
    voice_id: str # The voice ID corresponding to the agent's voice