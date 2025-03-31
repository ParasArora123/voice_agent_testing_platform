from models.agent import Agent

# For prototyping, we use an in-memory dictionary to store agents
agents = {
    "agent_001": Agent(
        id="agent_001",
        name="Test Agent",
        system_prompt="You are a helpful assistant.",
        llm_model_id="gpt-4o-mini",
        tts_model_id="eleven_flash_v2_5",
        stt_model_id="nova-3",
        voice_id="nPczCjzI2devNBz1zQrb"
    ),
    # Additional agents can be added here
}

def get_agent(agent_id: str) -> Agent:
    """
    Retrieve an agent from the database.
    """
    agent = agents.get(agent_id)
    if not agent:
        raise ValueError(f"Agent with ID {agent_id} not found.")
    
    return agent