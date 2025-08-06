from .onboarding import handle_chat_member_update, new_chat_member_message
from .admin import admin_panel, admin_callback_handler, logout_command
from .ranks import assign_rank, myrank, promoteme, demote
from .topic_guard import topic_guard
from ..web.webhook import healthcheck_handler, telegram_webhook_handler 

# Give proper alias names if you're exporting under different names
onboarding_handler = handle_chat_member_update
chat_member_handler = new_chat_member_message
assign_rank_command = assign_rank
my_rank_command = myrank
webhook_handler = telegram_webhook_handler

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