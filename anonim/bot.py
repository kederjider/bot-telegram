"""
Telegram Relay Bot
==================
Bot ini berfungsi sebagai pihak ketiga (relay) antara user dan developer.
Semua pesan (teks, video, audio, voice, foto, dokumen) dari user akan diteruskan ke developer,
dan developer bisa membalas langsung ke user via bot ini.

Cara kerja:
- User kirim pesan → Bot simpan arsip → Teruskan ke developer
- Developer balas dengan format: /reply <user_id> <pesan>  atau reply langsung ke pesan yang di-forward
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update, Message, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ParseMode

# ─────────────────────────────────────────────
#  LOAD ENVIRONMENT VARIABLES
# ─────────────────────────────────────────────
load_dotenv()

# ─────────────────────────────────────────────
#  KONFIGURASI  ← Baca dari .env file
# ─────────────────────────────────────────────
BOT_TOKEN    = os.getenv("BOT_TOKEN")              # Token dari @BotFather
DEVELOPER_ID = int(os.getenv("DEVELOPER_ID", 0))  # Chat ID developer (int)
ARCHIVE_DIR  = Path(os.getenv("ARCHIVE_DIR", "arsip"))  # Folder penyimpanan arsip lokal

# Validasi konfigurasi
if not BOT_TOKEN or BOT_TOKEN == "MASUKKAN_TOKEN_BOT_ANDA_DISINI":
    raise ValueError(
        "❌ BOT_TOKEN tidak ditemukan atau belum dikonfigurasi!\n"
        "   1. Salin .env.example ke .env\n"
        "   2. Edit .env dan masukkan BOT_TOKEN Anda\n"
        "   3. Jalankan bot kembali"
    )

if DEVELOPER_ID == 0:
    raise ValueError(
        "❌ DEVELOPER_ID tidak ditemukan atau belum dikonfigurasi!\n"
        "   1. Buka file .env\n"
        "   2. Ganti DEVELOPER_ID dengan Chat ID Anda\n"
        "   3. Jalankan bot kembali"
    )

# ─────────────────────────────────────────────

# Setup logging
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Buat direktori arsip
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
(ARCHIVE_DIR / "media").mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────
#  UTILITAS ARSIP
# ─────────────────────────────────────────────

def get_user_archive_path(user_id: int) -> Path:
    """Buat/ambil folder arsip per user."""
    p = ARCHIVE_DIR / str(user_id)
    p.mkdir(parents=True, exist_ok=True)
    return p


def save_archive_log(user_id: int, direction: str, msg_type: str, content: str, file_path: str = ""):
    """Simpan log percakapan ke file JSON."""
    archive_file = get_user_archive_path(user_id) / "log.json"

    if archive_file.exists():
        with open(archive_file, "r", encoding="utf-8") as f:
            logs = json.load(f)
    else:
        logs = []

    entry = {
        "timestamp": datetime.now().isoformat(),
        "direction": direction,   # "user→dev" atau "dev→user"
        "type": msg_type,
        "content": content,
        "file_path": file_path,
    }
    logs.append(entry)

    with open(archive_file, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


async def download_and_archive(file_obj, user_id: int, filename: str) -> str:
    """Unduh file dari Telegram dan simpan ke arsip lokal."""
    user_dir = get_user_archive_path(user_id) / "media"
    user_dir.mkdir(parents=True, exist_ok=True)
    local_path = user_dir / filename
    await file_obj.download_to_drive(str(local_path))
    return str(local_path)


def user_info_text(user) -> str:
    """Format info user menjadi teks ringkas."""
    name = user.full_name or "Tanpa Nama"
    username = f"@{user.username}" if user.username else "tidak ada username"
    return f"👤 *{name}* ({username})\n🆔 `{user.id}`"


# ─────────────────────────────────────────────
#  FORWARD KE DEVELOPER  (user → developer)
# ─────────────────────────────────────────────

async def forward_to_developer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler utama: terima semua pesan dari user lalu teruskan ke developer."""
    msg: Message = update.effective_message
    user = update.effective_user

    # Abaikan pesan dari developer sendiri
    if user.id == DEVELOPER_ID:
        return

    header = (
        f"📩 *Pesan Masuk dari User*\n"
        f"{user_info_text(user)}\n"
        f"{'─' * 30}"
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ── TEKS ──────────────────────────────────
    if msg.text:
        content = msg.text
        await context.bot.send_message(
            chat_id=DEVELOPER_ID,
            text=f"{header}\n\n💬 *Teks:*\n{content}",
            parse_mode=ParseMode.MARKDOWN,
        )
        save_archive_log(user.id, "user→dev", "text", content)
        logger.info("TEXT dari %s (%s) diteruskan ke developer.", user.full_name, user.id)

    # ── FOTO ──────────────────────────────────
    elif msg.photo:
        caption = msg.caption or ""
        photo   = msg.photo[-1]  # kualitas tertinggi
        file_obj = await context.bot.get_file(photo.file_id)
        fname    = f"{user.id}_{timestamp}_photo.jpg"
        local    = await download_and_archive(file_obj, user.id, fname)

        await context.bot.send_message(
            chat_id=DEVELOPER_ID,
            text=f"{header}\n\n🖼️ *Foto* (caption: {caption or '-'})\n📁 Arsip: `{local}`",
            parse_mode=ParseMode.MARKDOWN,
        )
        await context.bot.send_photo(
            chat_id=DEVELOPER_ID,
            photo=photo.file_id,
            caption=f"📸 Dari {user.full_name} (`{user.id}`)\n{caption}",
            parse_mode=ParseMode.MARKDOWN,
        )
        save_archive_log(user.id, "user→dev", "photo", caption, local)
        logger.info("PHOTO dari %s diteruskan.", user.full_name)

    # ── VIDEO ─────────────────────────────────
    elif msg.video:
        caption  = msg.caption or ""
        file_obj = await context.bot.get_file(msg.video.file_id)
        fname    = f"{user.id}_{timestamp}_video.mp4"
        local    = await download_and_archive(file_obj, user.id, fname)

        await context.bot.send_message(
            chat_id=DEVELOPER_ID,
            text=f"{header}\n\n🎬 *Video* (caption: {caption or '-'})\n📁 Arsip: `{local}`",
            parse_mode=ParseMode.MARKDOWN,
        )
        await context.bot.send_video(
            chat_id=DEVELOPER_ID,
            video=msg.video.file_id,
            caption=f"🎥 Dari {user.full_name} (`{user.id}`)\n{caption}",
            parse_mode=ParseMode.MARKDOWN,
        )
        save_archive_log(user.id, "user→dev", "video", caption, local)
        logger.info("VIDEO dari %s diteruskan.", user.full_name)

    # ── AUDIO / MP3 ───────────────────────────
    elif msg.audio:
        caption  = msg.caption or ""
        file_obj = await context.bot.get_file(msg.audio.file_id)
        fname    = f"{user.id}_{timestamp}_audio.mp3"
        local    = await download_and_archive(file_obj, user.id, fname)

        await context.bot.send_message(
            chat_id=DEVELOPER_ID,
            text=f"{header}\n\n🎵 *Audio/MP3* (caption: {caption or '-'})\n📁 Arsip: `{local}`",
            parse_mode=ParseMode.MARKDOWN,
        )
        await context.bot.send_audio(
            chat_id=DEVELOPER_ID,
            audio=msg.audio.file_id,
            caption=f"🎶 Dari {user.full_name} (`{user.id}`)\n{caption}",
            parse_mode=ParseMode.MARKDOWN,
        )
        save_archive_log(user.id, "user→dev", "audio", caption, local)
        logger.info("AUDIO dari %s diteruskan.", user.full_name)

    # ── VOICE NOTE ────────────────────────────
    elif msg.voice:
        file_obj = await context.bot.get_file(msg.voice.file_id)
        fname    = f"{user.id}_{timestamp}_voice.ogg"
        local    = await download_and_archive(file_obj, user.id, fname)

        await context.bot.send_message(
            chat_id=DEVELOPER_ID,
            text=f"{header}\n\n🎙️ *Voice Note*\n📁 Arsip: `{local}`",
            parse_mode=ParseMode.MARKDOWN,
        )
        await context.bot.send_voice(
            chat_id=DEVELOPER_ID,
            voice=msg.voice.file_id,
            caption=f"🎙️ Voice dari {user.full_name} (`{user.id}`)",
            parse_mode=ParseMode.MARKDOWN,
        )
        save_archive_log(user.id, "user→dev", "voice", "voice note", local)
        logger.info("VOICE dari %s diteruskan.", user.full_name)

    # ── DOKUMEN ───────────────────────────────
    elif msg.document:
        caption  = msg.caption or ""
        doc      = msg.document
        file_obj = await context.bot.get_file(doc.file_id)
        ext      = Path(doc.file_name).suffix if doc.file_name else ""
        fname    = f"{user.id}_{timestamp}_doc{ext}"
        local    = await download_and_archive(file_obj, user.id, fname)

        await context.bot.send_message(
            chat_id=DEVELOPER_ID,
            text=(
                f"{header}\n\n📄 *Dokumen:* `{doc.file_name}`\n"
                f"📦 Ukuran: {doc.file_size:,} bytes\n"
                f"📁 Arsip: `{local}`"
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
        await context.bot.send_document(
            chat_id=DEVELOPER_ID,
            document=doc.file_id,
            caption=f"📎 Dari {user.full_name} (`{user.id}`)\n{caption}",
            parse_mode=ParseMode.MARKDOWN,
        )
        save_archive_log(user.id, "user→dev", "document", doc.file_name or "", local)
        logger.info("DOCUMENT dari %s diteruskan.", user.full_name)

    # ── STICKER ───────────────────────────────
    elif msg.sticker:
        await context.bot.send_message(
            chat_id=DEVELOPER_ID,
            text=f"{header}\n\n🎭 *Stiker* dikirim oleh user.",
            parse_mode=ParseMode.MARKDOWN,
        )
        await context.bot.send_sticker(
            chat_id=DEVELOPER_ID,
            sticker=msg.sticker.file_id,
        )
        save_archive_log(user.id, "user→dev", "sticker", msg.sticker.emoji or "")

    # Konfirmasi ke user
    await msg.reply_text("✅ Pesan Anda telah diterima dan sedang diproses.")


# ─────────────────────────────────────────────
#  REPLY DARI DEVELOPER  (developer → user)
# ─────────────────────────────────────────────

async def developer_reply_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /reply <user_id> <pesan teks>
    Developer mengirim pesan teks ke user tertentu.
    """
    if update.effective_user.id != DEVELOPER_ID:
        await update.message.reply_text("⛔ Perintah ini hanya untuk developer.")
        return

    args = context.args
    if not args or len(args) < 2:
        await update.message.reply_text(
            "⚠️ Format: /reply <user_id> <pesan>\nContoh: /reply 123456789 Halo, ini balasan dari developer!"
        )
        return

    try:
        target_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ user_id harus berupa angka.")
        return

    text = " ".join(args[1:])
    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=f"💬 *Pesan dari Developer:*\n\n{text}",
            parse_mode=ParseMode.MARKDOWN,
        )
        await update.message.reply_text(f"✅ Pesan berhasil dikirim ke user `{target_id}`.", parse_mode=ParseMode.MARKDOWN)
        save_archive_log(target_id, "dev→user", "text", text)
        logger.info("Developer membalas TEXT ke user %s.", target_id)
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal mengirim: {e}")


async def developer_send_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Developer mengirim media ke user dengan format caption:
    /send_to <user_id>
    lalu lampirkan foto/video/audio/voice/dokumen dalam pesan yang sama.
    """
    if update.effective_user.id != DEVELOPER_ID:
        return

    msg = update.effective_message

    # Ambil user_id dari caption atau teks pesan
    raw = (msg.caption or msg.text or "").strip()
    if not raw.startswith("/send_to"):
        return

    parts = raw.split(maxsplit=1)
    if len(parts) < 2:
        await msg.reply_text("⚠️ Format: /send_to <user_id>  (kirim bersama media)")
        return

    try:
        target_id = int(parts[1].split()[0])
    except (ValueError, IndexError):
        await msg.reply_text("❌ user_id tidak valid.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    note      = "📩 *Pesan dari Developer*"

    try:
        # ── FOTO ──────────────────────────────
        if msg.photo:
            await context.bot.send_photo(
                chat_id=target_id,
                photo=msg.photo[-1].file_id,
                caption=f"{note}",
                parse_mode=ParseMode.MARKDOWN,
            )
            save_archive_log(target_id, "dev→user", "photo", "")

        # ── VIDEO ─────────────────────────────
        elif msg.video:
            await context.bot.send_video(
                chat_id=target_id,
                video=msg.video.file_id,
                caption=f"{note}",
                parse_mode=ParseMode.MARKDOWN,
            )
            save_archive_log(target_id, "dev→user", "video", "")

        # ── AUDIO ─────────────────────────────
        elif msg.audio:
            await context.bot.send_audio(
                chat_id=target_id,
                audio=msg.audio.file_id,
                caption=f"{note}",
                parse_mode=ParseMode.MARKDOWN,
            )
            save_archive_log(target_id, "dev→user", "audio", "")

        # ── VOICE ─────────────────────────────
        elif msg.voice:
            await context.bot.send_voice(
                chat_id=target_id,
                voice=msg.voice.file_id,
                caption=f"{note}",
                parse_mode=ParseMode.MARKDOWN,
            )
            save_archive_log(target_id, "dev→user", "voice", "")

        # ── DOKUMEN ───────────────────────────
        elif msg.document:
            await context.bot.send_document(
                chat_id=target_id,
                document=msg.document.file_id,
                caption=f"{note}",
                parse_mode=ParseMode.MARKDOWN,
            )
            save_archive_log(target_id, "dev→user", "document", msg.document.file_name or "")

        else:
            await msg.reply_text("⚠️ Tidak ada media yang dilampirkan.")
            return

        await msg.reply_text(f"✅ Media berhasil dikirim ke user `{target_id}`.", parse_mode=ParseMode.MARKDOWN)
        logger.info("Developer mengirim media ke user %s.", target_id)

    except Exception as e:
        await msg.reply_text(f"❌ Gagal mengirim ke user {target_id}: {e}")


# ─────────────────────────────────────────────
#  PERINTAH BOT
# ─────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id == DEVELOPER_ID:
        text = (
            "🛠️ *Mode Developer Aktif*\n\n"
            "Perintah tersedia:\n"
            "• `/reply <user_id> <pesan>` — balas teks ke user\n"
            "• `/send_to <user_id>` + lampirkan media — kirim media ke user\n"
            "• `/users` — lihat daftar user yang pernah menghubungi\n"
            "• `/history <user_id>` — lihat riwayat chat user\n"
        )
    else:
        text = (
            "👋 Halo! Saya adalah bot layanan pelanggan.\n\n"
            "Kirim pesan, foto, video, audio, voice note, atau dokumen — "
            "dan tim kami akan segera membalasnya! 📬"
        )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    logger.info("START dari %s (%s).", user.full_name, user.id)


async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/users — Tampilkan daftar user yang sudah menghubungi (khusus developer)."""
    if update.effective_user.id != DEVELOPER_ID:
        await update.message.reply_text("⛔ Perintah ini hanya untuk developer.")
        return

    user_dirs = [d for d in ARCHIVE_DIR.iterdir() if d.is_dir() and d.name.isdigit()]
    if not user_dirs:
        await update.message.reply_text("📭 Belum ada user yang menghubungi.")
        return

    lines = ["👥 *Daftar User:*\n"]
    for d in sorted(user_dirs):
        log_file = d / "log.json"
        count = 0
        last  = "-"
        if log_file.exists():
            with open(log_file, "r") as f:
                logs = json.load(f)
            count = len(logs)
            last  = logs[-1]["timestamp"][:16] if logs else "-"
        lines.append(f"• `{d.name}` — {count} pesan | terakhir: {last}")

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)


async def user_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/history <user_id> — Tampilkan riwayat percakapan user."""
    if update.effective_user.id != DEVELOPER_ID:
        await update.message.reply_text("⛔ Perintah ini hanya untuk developer.")
        return

    args = context.args
    if not args:
        await update.message.reply_text("⚠️ Format: /history <user_id>")
        return

    try:
        uid = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ user_id harus berupa angka.")
        return

    log_file = ARCHIVE_DIR / str(uid) / "log.json"
    if not log_file.exists():
        await update.message.reply_text(f"📭 Tidak ada riwayat untuk user `{uid}`.", parse_mode=ParseMode.MARKDOWN)
        return

    with open(log_file, "r") as f:
        logs = json.load(f)

    lines = [f"📋 *Riwayat user `{uid}`:*\n"]
    for entry in logs[-20:]:  # tampilkan 20 terakhir
        arah  = "⬆️" if entry["direction"] == "user→dev" else "⬇️"
        waktu = entry["timestamp"][:16]
        tipe  = entry["type"]
        isi   = entry["content"][:60] + ("…" if len(entry["content"]) > 60 else "")
        lines.append(f"{arah} `{waktu}` [{tipe}] {isi}")

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Perintah umum
    app.add_handler(CommandHandler("start", start))

    # Perintah developer
    app.add_handler(CommandHandler("reply",   developer_reply_text))
    app.add_handler(CommandHandler("users",   list_users))
    app.add_handler(CommandHandler("history", user_history))

    # Media dari developer ke user (/send_to <id> + lampiran)
    app.add_handler(MessageHandler(
        filters.User(DEVELOPER_ID) & (
            filters.PHOTO | filters.VIDEO | filters.AUDIO |
            filters.VOICE | filters.Document.ALL
        ),
        developer_send_media,
    ))

    # Semua pesan masuk dari user (bukan developer)
    app.add_handler(MessageHandler(
        ~filters.User(DEVELOPER_ID) & ~filters.COMMAND,
        forward_to_developer,
    ))

    logger.info("🤖 Bot relay aktif. Tekan Ctrl+C untuk berhenti.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
