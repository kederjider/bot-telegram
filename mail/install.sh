#!/bin/bash

# Instalasi Systemd Service untuk Telegram Email Bot
# Jalankan dengan: sudo bash install.sh

set -e

echo "📦 Instalasi Systemd Service untuk Telegram Email Bot..."
echo ""

# Validasi user root
if [[ $EUID -ne 0 ]]; then
    echo "❌ Skrip ini harus dijalankan sebagai root (gunakan: sudo bash install.sh)"
   exit 1
fi

# Konfigurasi
BOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
BOT_USER="botuser"
BOT_HOME="/home/$BOT_USER"
BOT_PATH="$BOT_HOME/telegram-email-bot"

echo "🔧 Konfigurasi:"
echo "   - Bot Directory: $BOT_DIR"
echo "   - Bot User: $BOT_USER"
echo "   - Bot Path: $BOT_PATH"
echo ""

# 1. Buat user bot jika belum ada
if ! id "$BOT_USER" &>/dev/null; then
    echo "👤 Membuat user $BOT_USER..."
    useradd -m -s /bin/bash "$BOT_USER"
else
    echo "✅ User $BOT_USER sudah ada"
fi

# 2. Copy bot directory jika belum ada di path yang benar
if [ "$BOT_DIR" != "$BOT_PATH" ]; then
    echo "📂 Menyalin bot ke $BOT_PATH..."
    mkdir -p "$BOT_PATH"

    if [ -f "$BOT_DIR/email.py" ]; then
        cp -f "$BOT_DIR/email.py" "$BOT_PATH/email.py"
        [ -f "$BOT_DIR/.env.example" ] && cp -f "$BOT_DIR/.env.example" "$BOT_PATH/.env.example"
        [ -f "$BOT_DIR/requirements.txt" ] && cp -f "$BOT_DIR/requirements.txt" "$BOT_PATH/requirements.txt"
        [ -f "$BOT_DIR/telegram-email-bot.service" ] && cp -f "$BOT_DIR/telegram-email-bot.service" "$BOT_PATH/telegram-email-bot.service"
        echo "✅ File bot berhasil disalin dari $BOT_DIR"
    else
        echo "⚠️  email.py tidak ditemukan di $BOT_DIR, lewati proses copy lokal."
        echo "   Script akan lanjut dan mengunduh file yang dibutuhkan dari repository."
    fi

    chown -R "$BOT_USER:$BOT_USER" "$BOT_PATH"
fi

# 3. Setup Python virtual environment
echo "🐍 Setup Python virtual environment..."
cd "$BOT_PATH"

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    chown -R "$BOT_USER:$BOT_USER" .venv
fi

# 4. Install dependencies
echo "📚 Install dependencies..."
sudo -u "$BOT_USER" .venv/bin/pip install --upgrade pip
sudo -u "$BOT_USER" .venv/bin/pip install python-telegram-bot python-dotenv

# 5. Cek .env file
if [ ! -f ".env" ]; then
    echo "⚠️  File .env tidak ditemukan!"
    echo "Pilih cara konfigurasi .env:"
    echo "  1) Edit sendiri (manual)"
    echo "  2) Isi sekarang (otomatis via prompt)"
    read -p "Masukkan pilihan [1/2]: " ENV_CHOICE

    if [ "$ENV_CHOICE" = "1" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            chown "$BOT_USER:$BOT_USER" .env
            echo "✅ .env dibuat dari .env.example"
        else
            touch .env
            chown "$BOT_USER:$BOT_USER" .env
            echo "✅ .env kosong berhasil dibuat"
        fi
        echo "✏️  Silakan edit file: $BOT_PATH/.env"
        echo "   Lalu jalankan lagi: sudo bash install.sh"
        exit 1
    elif [ "$ENV_CHOICE" = "2" ]; then
        read -p "Masukkan BOT_TOKEN: " BOT_TOKEN_INPUT
        read -p "Masukkan DEVELOPER_ID: " DEVELOPER_ID_INPUT
        read -p "Masukkan APP_PASSWORD_GMAIL: " APP_PASSWORD_INPUT
        read -p "Masukan EMAIL_SENDER (contoh: emailkamu@gmail): " EMAIL_SENDER_INPUT
        echo ""

        cat > "$BOT_PATH/.env" << END
        BOT_TOKEN=$BOT_TOKEN_INPUT
        AUTHORIZED_CHAT_ID=$DEVELOPER_ID_INPUT
        AUTHORIZED_CHAT_ID2=123456789
        AUTHORIZED_CHAT_ID3=123456789
        SMTP_SERVER=smtp.gmail.com
        SMTP_PORT=587
        EMAIL_SENDER=$EMAIL_SENDER_INPUT
        EMAIL_PASSWORD=$APP_PASSWORD_INPUT
END
        chown "$BOT_USER:$BOT_USER" .env
        echo "✅ .env berhasil dibuat otomatis"
    else
        echo "❌ Pilihan tidak valid. Jalankan ulang script dan pilih 1 atau 2."
        exit 1
    fi
else
    echo "✅ File .env ditemukan"
fi

# buat download email.py jika belum ada
if [ ! -f "$BOT_PATH/email.py" ]; then
    echo "📥 Mengunduh email.py..."
    wget -q -O "$BOT_PATH/email.py" "https://raw.githubusercontent.com/kederjider/bot-telegram/main/mail/email.py"
    chown "$BOT_USER:$BOT_USER" "$BOT_PATH/email.py"
fi

# 6. Install systemd service
echo "🚀 Menginstall systemd service..."
#cp telegram-email-bot.service /etc/systemd/system/
wget -q -O /etc/systemd/system/telegram-email-bot.service "https://raw.githubusercontent.com/kederjider/bot-telegram/main/mail/telegram-email-bot.service"
systemctl daemon-reexec
systemctl daemon-reload

# 7. Enable service
echo "⚙️  Mengaktifkan service..."
systemctl enable telegram-email-bot.service

# 8. Start service
echo "▶️  Menjalankan service..."
systemctl start telegram-email-bot.service

# 9. Status check
echo ""
echo "✅ Instalasi selesai!"
echo ""
echo "📋 Perintah berguna:"
echo "   • Cek status:  sudo systemctl status telegram-email-bot"
echo "   • Mulai:       sudo systemctl start telegram-email-bot"
echo "   • Stop:        sudo systemctl stop telegram-email-bot"
echo "   • Restart:     sudo systemctl restart telegram-email-bot"
echo "   • Log:         sudo journalctl -u telegram-email-bot -f"
echo ""
sleep 3
# Status service
sudo systemctl status telegram-email-bot --no-pager