from enum import Enum

class AgentState(Enum):
    LOADING = "loading"
    INIT = "init"
    RUNNING = "running"
    AWAITING_USER_INPUT = "awaiting_user_input"
    PAUSED = "paused"
    STOPPED = "stopped"
    FINISHED = "finished"
    ERROR = "error"

def is_agent_state_command(command: str) -> bool:
    return command in [e.value for e in AgentState]