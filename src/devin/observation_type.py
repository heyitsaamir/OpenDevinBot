from enum import Enum

class ObservationType(Enum):
    READ = "read"
    WRITE = "write"
    BROWSE = "browse"
    RUN = "run"
    RUN_IPYTHON = "run_ipython"
    RECALL = "recall"
    CHAT = "chat"
    AGENT_STATE_CHANGED = "agent_state_changed"