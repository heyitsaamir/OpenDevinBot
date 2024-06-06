from botbuilder.core import TurnContext, CardFactory
from botbuilder.schema import (
    ConversationReference,
    Activity
)
from typing import Optional, List, Dict, Any

from .devin_socket import DevinSocket
from .agent_state import AgentState, is_agent_state_command
from .action_type import ActionType
from .observation_type import ObservationType
from .commands import send_message, initialize_agent, clear_messages, start_message, stop_task
from .response_type import buildSocketMessage, DevinSocketMessage, ActionMessage, ObservationMessage
from .devin_auth import TokenStorage
from .devin_api import DevinAPI

import asyncio

def call_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    else:
        return loop.run_until_complete(coro)

TERMINAL_STATES = [AgentState.INIT.value, AgentState.STOPPED.value, AgentState.ERROR.value, AgentState.FINISHED.value]
    
class DevinConversationHandler:
    def __init__(self, 
                 context: TurnContext,
                 conversation_reference: Optional[ConversationReference], 
                 agent_state: Optional[AgentState],
                 app_id: str) -> None:
        self.__context = context
        self.__user_id = context.activity.from_property.aad_object_id # type: ignore
        self.__socket = DevinSocket(self.__user_id)
        self.__conversation_reference = conversation_reference
        self.__agent_state = agent_state or AgentState.INIT.value
        self.__app_id = app_id
        self.__socket.register_callback("receive", lambda _, event: self.__on_handle_assistant_message(event))
        self.__socket.register_callback("disconnect", lambda _, event: self.__on_close_socket(event))
        self.__socket.register_callback("connect", lambda _: self.__on_connect())
        self.__socket.initialize()
    
    async def handle_message(self, context: TurnContext, message: str):
        if (is_agent_state_command(message)):
            await self._handle_command(context, message)
            return
        
        if (self.__agent_state == AgentState.AWAITING_USER_INPUT.value):
            print(f"Got task message responding to user input {message}")
            self.__socket.send(send_message(message))
            return
        
        if (self.__is_running()):
            await context.send_activity('There is already a task running. Please wait until it finishes. Or use a command to interrupt it')
            return
        await self._handle_new_task(message)
    
    async def _handle_command(self, context: TurnContext, command: str):
        print(f"Got task command {command}")
        if (command == AgentState.STOPPED.value):
            self.__socket.send(stop_task())
            await context.send_activity("Task stopped.")
        else:
            await self.__context.send_activity("There is no task running. Please start a task first.")
            
    async def _handle_new_task(self, message: str):
        self.__original_message = message
        self.__socket.send(initialize_agent())
    
    def __on_handle_assistant_message(self, event):
        assert isinstance(event, str)
        socket_message = buildSocketMessage(event)
        if isinstance(socket_message, ObservationMessage) and socket_message.observation == ObservationType.AGENT_STATE_CHANGED.value:
            self._handle_assistant_state_changed(socket_message)
            
        if self.__is_running() or (isinstance(socket_message, ActionMessage) and socket_message.action == ActionType.FINISH.value):
            self._handle_assistant_message(socket_message)
        
    def _handle_assistant_state_changed(self, socket_message: ObservationMessage):
        if socket_message.extras is not None and socket_message.extras.get('agent_state') is not None:
            # keep track of the agent_state
            if self.__agent_state != socket_message.extras.get('agent_state'):
                print(f"Agent state changed to {socket_message.extras.get('agent_state')}")
            self.__agent_state = socket_message.extras.get('agent_state')
            
            if self.__agent_state == AgentState.INIT.value:
                print("Clearing messages...")
                self.__socket.send(clear_messages())
                print("Sending start message...")
                self.__socket.send(start_message(self.__original_message))
                return True
            elif self.__agent_state == AgentState.FINISHED.value or self.__agent_state == AgentState.STOPPED.value:
                return True
        return False # indicate that this is not a terminal state
    
    def _handle_assistant_message(self, socket_message: DevinSocketMessage):
        message_to_send = None
        if isinstance(socket_message, ActionMessage):
            args_content = socket_message.args.get('content')
            wait_for_response = socket_message.args.get('wait_for_response')
            message = socket_message.message
            thought = socket_message.args.get('thought')
            match socket_message.action:
                case ActionType.INIT.value:
                    pass
                case ActionType.MESSAGE.value:
                    if args_content is not None:
                        message_to_send = build_adaptive_card(args_content, "QuestionCircle" if wait_for_response else "Lightbulb")
                case ActionType.FINISH.value:
                    message_to_send = build_adaptive_card(message, "CheckboxChecked")
                case ActionType.CHANGE_AGENT_STATE.value:
                    pass
                case _:
                    if thought:
                        message_to_send = build_adaptive_card(thought, "Glasses")
        elif isinstance(socket_message, ObservationMessage) and socket_message.message is not None and socket_message.message != '':
            message = socket_message.message
            match socket_message.observation:
                case ObservationType.RUN.value:
                    pass
                case ObservationType.AGENT_STATE_CHANGED.value:
                    pass
                case ObservationType.BROWSE.value:
                    pass
                case ObservationType.WRITE.value:
                    message_to_send = build_adaptive_card(message, "Folder")
                case _:
                    if message:
                        message_to_send = build_adaptive_card(message, "Glasses")

        if message_to_send:
            call_async(self.__context.adapter.continue_conversation(
                self.__conversation_reference,
                lambda context: context.send_activity(message_to_send),
                self.__app_id,
            ))
    
    def __on_close_socket(self, event):
        print("Socket closed for agent")
        
    def __on_connect(self):
        token = TokenStorage().get_token(self.__user_id)
        messages = DevinAPI.fetch_messages(token)
        for message in messages:
            if isinstance(message, ObservationMessage) and message.observation == ObservationType.AGENT_STATE_CHANGED.value:
                self._handle_assistant_state_changed(message)
        
    def __is_running(self):
        return self.__agent_state not in TERMINAL_STATES and self.__agent_state is not None

def build_adaptive_card(msg: str, icon: str, is_important: Optional[bool] = None, url: Optional[str] = None) -> Activity:
    body: List[Dict[str, Any]] = [
        {
            "type": "ColumnSet",
            "columns": [
                {
                    "type": "Column",
                    "width": "auto",
                    "items": [
                        {
                            "type": "Icon",
                            "name": f"{icon}",
                            "style": "Regular",
                            "color": "Accent",
                        },
                    ],
                },
                {
                    "type": "Column",
                    "width": "stretch",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": f"{msg}",
                            "wrap": True,
                            "fontType": "Monospace",
                            "weight": "Lighter",
                            "isSubtle": True,
                        },
                    ],
                },
            ],
        },
    ]

    if url is not None:
        body.append({
            "type": "ActionSet",
            "actions": [
                {
                    "type": "Action.OpenUrl",
                    "title": "Open",
                    "url": url,
                },
            ],
        })

    ac = CardFactory.adaptive_card({
        "type": "AdaptiveCard",
        "body": body,
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.6",
    })

    return Activity(
        attachments=[ac],
        importance="High" if is_important else "Normal",
        summary=msg,
    )
