import os
import smtplib
import logging
from email.message import EmailMessage
from dotenv import load_dotenv

from telegram import (
    Message,
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# ===== LOAD ENV =====
load_dotenv()

def require_env(name: str, value: str | None) -> str:
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


BOT_TOKEN = require_env("BOT_TOKEN", os.getenv("BOT_TOKEN"))


def _load_authorized_chat_ids() -> set[int]:
    # Support multiple authorized chat IDs from separate env vars.
    keys = ["AUTHORIZED_CHAT_ID", "AUTHORIZED_CHAT_ID2", "AUTHORIZED_CHAT_ID3"]
    ids: set[int] = set()
    for key in keys:
        value = os.getenv(key)
        if not value:
            continue
        try:
            ids.add(int(value.strip()))
        except ValueError:
            logging.warning("Invalid %s value in .env: %r", key, value)
    return ids


AUTHORIZED_CHAT_IDS = _load_authorized_chat_ids()

SMTP_SERVER = require_env("SMTP_SERVER", os.getenv("SMTP_SERVER"))
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_SENDER = require_env("EMAIL_SENDER", os.getenv("EMAIL_SENDER"))
EMAIL_PASSWORD = require_env("EMAIL_PASSWORD", os.getenv("EMAIL_PASSWORD"))

# ===== LOGGING =====
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ===== STATES =====
MENU, TO, SUBJECT, BODY, FILE = range(5)

# ===== UTIL =====
def is_authorized(update: Update) -> bool:
    return bool(update.effective_chat and update.effective_chat.id in AUTHORIZED_CHAT_IDS)


def get_message(update: Update) -> Message | None:
    return update.effective_message

def send_email(to_addr: str, subject: str, body: str, attachment_path: str | None):
    msg = EmailMessage()
    msg["From"] = EMAIL_SENDER
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body or "")

    if attachment_path:
        with open(attachment_path, "rb") as f:
            data = f.read()
            filename = os.path.basename(attachment_path)
        # default generic type
        msg.add_attachment(data, maintype="application", subtype="octet-stream", filename=filename)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)

# ===== HANDLERS =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = get_message(update)
    if message is None:
        return ConversationHandler.END

    if not is_authorized(update):
        await message.reply_text(
            "Maaf user_id tidak terdaftar, silakan hubungi t.me/tuan_mubot untuk mendapatkan akses."
        )
        return

    keyboard = [["📧 Kirim Email", "❌ Batal"]]
    await message.reply_text(
        "Pilih menu:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return MENU

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = get_message(update)
    if message is None:
        return ConversationHandler.END

    if not is_authorized(update):
        return ConversationHandler.END

    text = message.text or ""
    if text == "📧 Kirim Email":
        await message.reply_text("Masukkan email tujuan:", reply_markup=ReplyKeyboardRemove())
        return TO
    else:
        await message.reply_text("Dibatalkan.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

async def get_to(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = get_message(update)
    if message is None:
        return ConversationHandler.END

    if not is_authorized(update):
        return ConversationHandler.END

    to_addr = (message.text or "").strip()
    if "@" not in to_addr or len(to_addr) > 200:
        await message.reply_text("Format email tidak valid. Coba lagi:")
        return TO

    user_data = context.user_data or {}
    user_data["to"] = to_addr
    await message.reply_text("Masukkan subject:")
    return SUBJECT

async def get_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = get_message(update)
    if message is None:
        return ConversationHandler.END

    if not is_authorized(update):
        return ConversationHandler.END

    subject = (message.text or "").strip()
    if not subject:
        await message.reply_text("Subject tidak boleh kosong. Coba lagi:")
        return SUBJECT

    user_data = context.user_data or {}
    user_data["subject"] = subject
    await message.reply_text("Masukkan isi pesan (atau ketik '-' jika hanya kirim file):")
    return BODY

async def get_body(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = get_message(update)
    if message is None:
        return ConversationHandler.END

    if not is_authorized(update):
        return ConversationHandler.END

    body = message.text or ""
    if body.strip() == "-":
        body = ""

    # simple limit
    if len(body) > 5000:
        await message.reply_text("Pesan terlalu panjang (maks 5000). Coba lagi:")
        return BODY

    user_data = context.user_data or {}
    user_data["body"] = body
    keyboard = [["⏭ Skip Lampiran"]]
    await message.reply_text(
        "Kirim file sekarang (opsional), atau tekan tombol Skip untuk tanpa lampiran.",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return FILE

async def get_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = get_message(update)
    if message is None:
        return ConversationHandler.END

    if not is_authorized(update):
        return ConversationHandler.END

    attachment_path = None

    # user skip via button or typed command
    text = message.text or ""
    if text.strip().lower() in {"skip", "⏭ skip lampiran"}:
        attachment_path = None
    elif message.document:
        # download file
        file = await message.document.get_file()
        filename = message.document.file_name or "attachment.bin"
        save_path = os.path.join("downloads", filename)
        os.makedirs("downloads", exist_ok=True)
        await file.download_to_drive(save_path)
        attachment_path = save_path
    else:
        await message.reply_text("Silakan kirim file, atau tekan tombol Skip.")
        return FILE

    # kirim email
    try:
        user_data = context.user_data or {}
        send_email(
            to_addr=user_data["to"],
            subject=user_data["subject"],
            body=user_data["body"],
            attachment_path=attachment_path
        )
        await message.reply_text("Email berhasil dikirim ✅", reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        logging.error(e)
        await message.reply_text("Gagal kirim email ❌", reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = get_message(update)
    if message is None:
        return ConversationHandler.END

    user_data = context.user_data or {}
    user_data.clear()
    await message.reply_text("Dibatalkan.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# ===== MAIN =====
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu)],
            TO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_to)],
            SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_subject)],
            BODY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_body)],
            FILE: [
                MessageHandler(filters.Document.ALL, get_file),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_file),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("batal", cancel),
        ],
    )

    app.add_handler(conv)

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()