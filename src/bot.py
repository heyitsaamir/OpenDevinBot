"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.

Description: initialize the app and listen for `message` activitys
"""

import sys
import traceback

from botbuilder.core import TurnContext
from teams import Application, ApplicationOptions, TeamsAdapter
from teams.state import TurnState
from typing import Dict
from devin_types.devin_conversation_handler import DevinConversationHandler

from config import Config

config = Config()
app = Application[TurnState](
    ApplicationOptions(
        bot_app_id=config.APP_ID,
        adapter=TeamsAdapter(config),
    )
)
  
def build_storage_key(conversation_id: str):
    return f"conversation_reference-{conversation_id}"
        
in_memory_conversation_dict: Dict[str, DevinConversationHandler] = {}    

@app.activity("message")
async def on_message(context: TurnContext, _state: TurnState):
    conversation_reference = TurnContext.get_conversation_reference(context.activity)
    conversation_id = conversation_reference.conversation.id # type: ignore
    storage = in_memory_conversation_dict.get(build_storage_key(conversation_id))
    if not storage:
        storage = DevinConversationHandler(
            context,
            conversation_reference,
            None,
            config.APP_ID
        )
        in_memory_conversation_dict[build_storage_key(conversation_id)] = storage

    await storage.handle_message(context, context.activity.text)
    return True


@app.error
async def on_error(context: TurnContext, error: Exception):
    # This check writes out errors to console log .vs. app insights.
    # NOTE: In production environment, you should consider logging this to Azure
    #       application insights.
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()

    # Send a message to the user
    await context.send_activity("The bot encountered an error or bug.")
