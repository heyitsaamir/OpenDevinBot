import json
from typing import Dict, Union, Any

class ActionMessage:
    def __init__(self, action: str, args: Dict[str, str] | None, message: str | None):
        self.action = action
        self.args = args or {}
        self.message = message or ""
        
    def __getattribute__(self, name: str) -> Any:
        return super().__getattribute__(name)

class ObservationMessage:
    def __init__(self, observation: str, 
                 content: str | None, 
                 extras: Dict[str, str] | None, 
                 message: str | None):
        self.observation = observation
        self.content = content
        self.extras = extras
        self.message = message
        # self.screenshot = screenshot # Not needed for this app
        
    def __getattribute__(self, name: str) -> Any:
        return super().__getattribute__(name)

DevinSocketMessage = Union[ActionMessage, ObservationMessage]

def buildSocketMessageFromDict(jsonObj: Dict[str, Any]) -> DevinSocketMessage:
    if 'action' in jsonObj:
        action = jsonObj.get('action')
        assert action is not None
        return ActionMessage(
            action=action,
            args=jsonObj.get('args'),
            message=jsonObj.get('message')
        )
    else:
        observation = jsonObj.get('observation')
        assert observation is not None
        return ObservationMessage(
            observation=observation,
            content=jsonObj.get('content'),
            extras=jsonObj.get('extras'),
            message=jsonObj.get('message')
        )

def buildSocketMessage(jsonStr: str) -> DevinSocketMessage:
    jsonObj = json.loads(jsonStr)
    return buildSocketMessageFromDict(jsonObj)