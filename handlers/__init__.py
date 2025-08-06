from .onboarding import handle_chat_member_update, new_chat_member_message, topic_guard_handler
from .admin import admin_panel, admin_callback_handler, logout_command
from .ranks import assign_rank, myrank, promoteme, demote
from web.webhook import telegram_webhook_handler, healthcheck_handler 

# Give proper alias names if you're exporting under different names
onboarding_handler = handle_chat_member_update
chat_member_handler = new_chat_member_message
assign_rank_command = assign_rank
my_rank_command = myrank
button_handler = admin_callback_handler
topic_guard = topic_guard_handler
webhook_handler = telegram_webhook_handler
status = healthcheck_handler

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
    "webhook_handler"
    "status"
]
