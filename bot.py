import os
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import Application, ChatMemberHandler, ContextTypes

TOKEN = os.environ["BOT_TOKEN"]

MAIN_CHAT_ID = -1003562568348
LOG_CHAT_ID = -5378556318

TZ = ZoneInfo("Asia/Yekaterinburg")

db = sqlite3.connect("history.db", check_same_thread=False)
db.execute("""
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username TEXT,
    full_name TEXT,
    event TEXT NOT NULL,
    event_time TEXT NOT NULL
)
""")
db.commit()


def user_text(user):
    name = user.full_name or "Без имени"
    username = f"@{user.username}" if user.username else "нет username"
    return name, username


async def member_changed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    change = update.chat_member

    if not change or change.chat.id != MAIN_CHAT_ID:
        return

    old_status = change.old_chat_member.status
    new_status = change.new_chat_member.status
    user = change.new_chat_member.user

    joined = (
        old_status in ("left", "kicked")
        and new_status in ("member", "administrator", "creator")
    )

    left = (
        old_status in ("member", "administrator", "creator")
        and new_status in ("left", "kicked")
    )

    if not joined and not left:
        return

    now = datetime.now(TZ)
    timestamp = now.strftime("%d.%m.%Y %H:%M:%S")

    name, username = user_text(user)

    if joined:
        event = "JOIN"
        title = "🟢 ВСТУПИЛ(А) В ГРУППУ"
    else:
        event = "REMOVED" if new_status == "kicked" else "LEFT"
        title = (
            "⛔️ УДАЛЁН(А) ИЗ ГРУППЫ"
            if event == "REMOVED"
            else "🔴 ВЫШЕЛ/ВЫШЛА ИЗ ГРУППЫ"
        )

    db.execute(
        """
        INSERT INTO events
        (user_id, username, full_name, event, event_time)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user.id, user.username, name, event, now.isoformat()),
    )
    db.commit()

    message = (
        f"{title}\n\n"
        f"👤 {name}\n"
        f"🔗 {username}\n"
        f"🆔 {user.id}\n"
        f"🕐 {timestamp}"
    )

    await context.bot.send_message(
        chat_id=LOG_CHAT_ID,
        text=message
    )


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        ChatMemberHandler(
            member_changed,
            ChatMemberHandler.CHAT_MEMBER
        )
    )

    print("Bot started")
    app.run_polling(
        allowed_updates=["chat_member"]
    )


if __name__ == "__main__":
    main()
