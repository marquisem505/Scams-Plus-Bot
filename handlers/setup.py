from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ChatMemberHandler,
    Application,
    filters,
)
from handlers.admin import (
    admin_panel, admin_callback_handler, logout_command,
    assign_rank_command, demote_command, my_rank_command, promote_me_command
)
from handlers.onboarding import (
    start_command, admin_password_handler, reply_forwarder,
    view_logs, button_handler, topic_guard_handler
)
from handlers.chat_events import (
    handle_join, new_chat_member_message
)

def setup_handlers(app: Application):
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("logout", logout_command))
    app.add_handler(CommandHandler("assignrank", assign_rank_command))
    app.add_handler(CommandHandler("demote", demote_command))
    app.add_handler(CommandHandler("myrank", my_rank_command))
    app.add_handler(CommandHandler("promoteme", promote_me_command))
    app.add_handler(CommandHandler("logs", view_logs))

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_chat_member_message))
    app.add_handler(ChatMemberHandler(handle_join, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, admin_password_handler))
    app.add_handler(MessageHandler(filters.TEXT & filters.REPLY, reply_forwarder))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), topic_guard_handler))

    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CallbackQueryHandler(admin_callback_handler))