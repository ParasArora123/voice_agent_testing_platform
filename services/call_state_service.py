import uuid

from config.config import call_states
from models.call_state import CallState

# TODO: In production, these should all be database operations and not stored just in memory with a dict

def get_call_state(call_state_id: str):
    """
    Retrieve the information associated with a call's stored state ID from the DB.
    """
    call_state_data = call_states.get(call_state_id)
    if not call_state_data:
        raise ValueError(f"No call state found for ID: {call_state_id}")
    
    return call_state_data

def add_call_state(vonage_uuid: str, agent_id: str, max_duration_sec: int = 180) -> str:
    """
    Add a new call state to the DB and return the generated call_state_id.
    """
    call_state_id = str(uuid.uuid4())
    new_state = CallState(
        id=call_state_id,
        vonage_uuid=vonage_uuid,
        agent_id=agent_id,
        max_duration_sec=max_duration_sec
    )

    call_states[call_state_id] = new_state

    print(f"Added call state {call_state_id} for Vonage UUID {vonage_uuid} with test agent {agent_id}")

    return call_state_id

def delete_call_state(call_state_id: str):
    """
    Delete a call state from the DB.
    """
    if call_state_id in call_states:
        del call_states[call_state_id]
        print(f"Removed call state: {call_state_id}. Remaining # of states: {len(call_states)}")
    else:
        print(f"Call state {call_state_id} not found in call_states")