import asyncio
from datetime import datetime, timezone
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .ai import ask_ai
from .config import (
    TELEGRAM_ALLOWED_USER_ID,
    TELEGRAM_BOT_TOKEN,
)
from .database import (
    get_recent_posts,
    save_chat_message,
)


# =========================
# HELPERS
# =========================

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_allowed(update: Update) -> bool:

    if not TELEGRAM_ALLOWED_USER_ID:
        return True

    user = update.effective_user

    if user is None:
        return False

    return str(user.id) == str(
        TELEGRAM_ALLOWED_USER_ID
    )


# =========================
# START COMMAND
# =========================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:

    if not is_allowed(update):

        await update.message.reply_text(
            "غير مصرح لك باستخدام هذا البوت."
        )

        return


    await update.message.reply_text(
        "🔭 X Radar AI جاهز.\n\n"
        "أرسل لي سؤالك عن الـ For You، مثل:\n\n"
        "• وش أكثر شيء كان يدور اليوم؟\n"
        "• ركز على AI\n"
        "• هات أفضل 5\n"
        "• وش الشيء الغريب؟\n"
        "• وش صار اليوم؟"
    )


# =========================
# HELP COMMAND
# =========================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:

    if not is_allowed(update):

        await update.message.reply_text(
            "غير مصرح لك باستخدام هذا البوت."
        )

        return


    await update.message.reply_text(
        "🔭 X Radar AI\n\n"
        "اسألني أي سؤال عن المنشورات "
        "التي جمعها النظام من For You."
    )


# =========================
# MESSAGE HANDLER
# =========================

async def message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:

    if not is_allowed(update):

        await update.message.reply_text(
            "غير مصرح لك باستخدام هذا البوت."
        )

        return


    if update.message is None:
        return


    question = update.message.text

    if not question:
        return


    question = question.strip()

    if not question:
        return


    # -------------------------
    # Save user message
    # -------------------------

    save_chat_message(
        role="user",
        content=question,
        created_at=utc_now()
    )


    # -------------------------
    # Loading message
    # -------------------------

    loading = await update.message.reply_text(
        "🔭 أحلل الـFor You..."
    )


    try:

        # -------------------------
        # Get recent posts
        # -------------------------

        posts = get_recent_posts(
            limit=150
        )


        # -------------------------
        # Ask AI
        # -------------------------

        answer = await ask_ai(
            question=question,
            posts=posts
        )


        # -------------------------
        # Save AI answer
        # -------------------------

        save_chat_message(
            role="assistant",
            content=answer,
            created_at=utc_now()
        )


        # -------------------------
        # Send answer
        # -------------------------

        await loading.edit_text(
            answer
        )


    except Exception as error:

        print(
            "Telegram handler error:",
            error
        )

        await loading.edit_text(
            "حدث خطأ أثناء تحليل البيانات."
        )


# =========================
# TELEGRAM APPLICATION
# =========================

def create_application() -> Optional[Application]:

    if not TELEGRAM_BOT_TOKEN:

        print(
            "TELEGRAM_BOT_TOKEN is not configured."
        )

        return None


    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )


    application.add_handler(
        CommandHandler(
            "start",
            start_command
        )
    )


    application.add_handler(
        CommandHandler(
            "help",
            help_command
        )
    )


    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            message_handler
        )
    )


    return application


# =========================
# RUN TELEGRAM BOT
# =========================

async def telegram_loop() -> None:

    application = create_application()

    if application is None:
        return


    print(
        "Starting Telegram bot..."
    )


    await application.initialize()

    await application.start()

    await application.updater.start_polling()


    try:

        while True:

            await asyncio.sleep(3600)

    finally:

        await application.updater.stop()

        await application.stop()

        await application.shutdown()
