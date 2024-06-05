from .action_type import ActionType
from .agent_state import AgentState

def initialize_agent():
    event = {"action": ActionType.INIT.value, "args": {
        "LLM_MODEL": "gpt-4o",
        "AGENT": "PlannerAgent",
        "LANGUAGE": "English",
    }}
    return event

def start_message(message):
    event = {"action": ActionType.START.value, "args": {
        "task": message
    }}
    return event

def send_message(message):
    event = {"action": ActionType.MESSAGE.value, "args": {
        "content": message
    }}
    return event

def clear_messages():
    event = {"action": ActionType.CLEAR_MESSAGES.value, "args": {}}
    return event

def stop_task():
    event = {
            "action": ActionType.CHANGE_AGENT_STATE.value,
            "args": {"agent_state": AgentState.STOPPED.value},
        }
    return event