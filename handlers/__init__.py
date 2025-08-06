from .onboarding import handle_chat_member_update, new_chat_member_message, topic_guard_handler
from .admin import admin_panel, admin_callback_handler, logout_command
from .ranks import assign_rank, myrank, promoteme, demote

# Give proper alias names if you're exporting under different names
onboarding_handler = handle_chat_member_update
chat_member_handler = new_chat_member_message
assign_rank_command = assign_rank
my_rank_command = myrank
button_handler = admin_callback_handler
topic_guard = topic_guard_handler

# --- Exported Handlers ---
__all__ = [
    "onboarding_handler",
    "chat_member_handler",
    "admin_panel",
    "admin_callback_handler",
    "logout_command",
    "assign_rank_command",
    "my_rank_command",
    "promoteme",
    "demote",
    "topic_guard",
    "healthcheck_handler",
    "webhook_handler"
]
# handlers/__init__.py
from .admin import admin_panel, admin_callback_handler, logout_command
from .ranks import assign_rank, demote, myrank, promoteme
from .onboarding import (
    start_command,
    handle_private_message,
    button_handler,
    topic_guard_handler,
    view_logs,
    reply_forwarder,
    handle_chat_member_update,
    new_chat_member_message
)