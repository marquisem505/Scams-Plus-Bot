from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ChatMemberHandler,
    Application,
    filters,
)
from handlers.admin import (
    admin_panel,
    admin_callback_handler,
    logout_command,
    handle_private_message,
)
from handlers.onboarding import (
    start_command,
    handle_private_message),
    reply_forwarder,
    view_logs,
    button_handler,
    topic_guard_handler,
)
from handlers.chat_events import handle_join, new_chat_member_message
from handlers.ranks import set_user_rank, demote, myrank, promoteme


def setup_handlers(app: Application):
    # Command Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("logout", logout_command))
    app.add_handler(CommandHandler("assignrank", set_user_rank))
    app.add_handler(CommandHandler("demote", demote))
    app.add_handler(CommandHandler("myrank", myrank))
    app.add_handler(CommandHandler("promoteme", promoteme))
    app.add_handler(CommandHandler("logs", view_logs))

    # Message Handlers
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_chat_member_message))
    app.add_handler(ChatMemberHandler(handle_join, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.TEXT & filters.REPLY, reply_forwarder))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, topic_guard_handler))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_private_message))

    # Callback Query Handlers
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CallbackQueryHandler(admin_callback_handler))