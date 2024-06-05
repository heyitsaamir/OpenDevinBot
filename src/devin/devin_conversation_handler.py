"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.

Description: initialize the app and listen for `message` activitys
"""

import json
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

import asyncio

def call_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    else:
        return loop.run_until_complete(coro)

TERMINAL_STATES = [AgentState.INIT.value, AgentState.FINISHED.value, AgentState.STOPPED.value, AgentState.ERROR.value]
    
class DevinConversationHandler:
    def __init__(self, 
                 context: TurnContext,
                 conversation_reference: Optional[ConversationReference], 
                 agent_state: Optional[AgentState],
                 app_id: str) -> None:
        self.context = context
        self.socket = DevinSocket(context.activity.from_property.aad_object_id) # type: ignore
        self.conversation_reference = conversation_reference
        self.agent_state = agent_state
        self.app_id = app_id
    
    async def handle_message(self, context: TurnContext, message: str):
        if (is_agent_state_command(message)):
            await self._handle_command(context, message)
            return
        
        if (self.agent_state == AgentState.AWAITING_USER_INPUT.value):
            print(f"Got task message responding to user input {message}")
            self.socket.send(send_message(message))
            return
        
        if (self._is_running()):
            await context.send_activity('There is already a task running. Please wait until it finishes. Or use a command to interrupt it')
            return
        await self._handle_new_task(message)
    
    async def _handle_command(self, context: TurnContext, command: str):
        print(f"Got task command {command}")
        if (self._is_running() and command == AgentState.STOPPED.value):
            self.socket.send(stop_task())
            await context.send_activity("Task stopped.")
        else:
            await self.context.send_activity("There is no task running. Please start a task first.")
            
    async def _handle_new_task(self, message: str):
        self.socket.unregister_all_callbacks()
        self.socket.register_callback("receive", lambda _, event: self._on_handle_assistant_message(event))
        self.socket.register_callback("disconnect", lambda _, event: self._on_close_socket(event))
        self.original_message = message
        self.socket.send(initialize_agent())
    
    def _on_handle_assistant_message(self, event):
        assert isinstance(event, str)
        socket_message = buildSocketMessage(event)
        if isinstance(socket_message, ObservationMessage) and socket_message.observation == ObservationType.AGENT_STATE_CHANGED.value:
            self._handle_assistant_state_changed(socket_message)
            
        if not self._is_running():
            self._handle_assistant_message(socket_message)
        
    def _handle_assistant_state_changed(self, socket_message: ObservationMessage):
        if socket_message.extras is not None and socket_message.extras.get('agent_state') is not None:
            # keep track of the agent_state
            self.agent_state = socket_message.extras.get('agent_state')
            
            if self.agent_state == AgentState.INIT.value:
                print("Clearing messages...")
                self.socket.send(clear_messages())
                print("Sending start message...")
                self.socket.send(start_message(self.original_message))
                return True
            elif self.agent_state == AgentState.FINISHED.value or self.agent_state == AgentState.STOPPED.value:
                return True
        return False # indicate that this is not a terminal state
    
    def _handle_assistant_message(self, socket_message: DevinSocketMessage):
        message_to_send = None
        if isinstance(socket_message, ActionMessage):
            args_content = socket_message.args.get('content')
            wait_for_response = socket_message.args.get('wait_for_response')
            message = socket_message.message
            thought = socket_message.args.get('thought')
            if socket_message.action == ActionType.INIT.value:
                return
            elif socket_message.action == ActionType.MESSAGE.value and args_content is not None:
                message_to_send = build_adaptive_card(args_content, "QuestionCircle" if wait_for_response else "Lightbulb")
            elif socket_message.action == ActionType.FINISH.value:
                message_to_send = build_adaptive_card(message, "CheckboxChecked")
            elif socket_message.action == ActionType.CHANGE_AGENT_STATE.value:
                pass
            elif thought:
                message_to_send = build_adaptive_card(thought, "Glasses")
        elif isinstance(socket_message, ObservationMessage) and socket_message.message is not None and socket_message.message != '':
            message = socket_message.message
            if socket_message.observation == ObservationType.WRITE.value:
                message_to_send = build_adaptive_card(message, "Folder")
            else:
                message_to_send = build_adaptive_card(message, "Glasses")

        if message_to_send:
            call_async(self.context.adapter.continue_conversation(
                self.conversation_reference,
                lambda context: context.send_activity(message_to_send),
                self.app_id,
            ))
    
    def _on_close_socket(self, event):
        print("Socket closed for agent")
        
    def _is_running(self):
        return self.agent_state not in TERMINAL_STATES

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
