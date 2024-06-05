from enum import Enum

class ActionType(Enum):
    INIT = "initialize"
    START = "start"
    MESSAGE = "message"
    READ = "read"
    WRITE = "write"
    RUN = "run"
    RUN_IPYTHON = "run_ipython"
    KILL = "kill"
    BROWSE = "browse"
    RECALL = "recall"
    FINISH = "finish"
    ADD_TASK = "add_task"
    MODIFY_TASK = "modify_task"
    CHANGE_AGENT_STATE = "change_agent_state"
    CLEAR_MESSAGES = "clear_messages"