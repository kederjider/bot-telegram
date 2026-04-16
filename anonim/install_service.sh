#!/bin/bash

# Instalasi Systemd Service untuk Telegram Relay Bot
# Jalankan dengan: sudo bash install_service.sh

set -e

echo "📦 Instalasi Systemd Service untuk Telegram Relay Bot..."
echo ""

# Validasi user root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Skrip ini harus dijalankan sebagai root (gunakan: sudo bash install_service.sh)"
   exit 1
fi

# Konfigurasi
BOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
BOT_USER="botuser"
BOT_HOME="/home/$BOT_USER"
BOT_PATH="$BOT_HOME/telegram-relay-bot"

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
    mkdir -p "$(dirname "$BOT_PATH")"
    cp -r "$BOT_DIR"/* "$BOT_PATH/"
    chown -R "$BOT_USER:$BOT_USER" "$BOT_PATH"
fi

# 3. Setup Python virtual environment
echo "🐍 Setup Python virtual environment..."
cd "$BOT_PATH"

if [ ! -d "venv" ]; then
    python3 -m venv venv
    chown -R "$BOT_USER:$BOT_USER" venv
fi

# 4. Install dependencies
echo "📚 Install dependencies..."
sudo -u "$BOT_USER" venv/bin/pip install --upgrade pip
sudo -u "$BOT_USER" venv/bin/pip install python-telegram-bot python-dotenv

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
        echo "   Lalu jalankan lagi: sudo bash install_service.sh"
        exit 1
    elif [ "$ENV_CHOICE" = "2" ]; then
        read -p "Masukkan BOT_TOKEN: " BOT_TOKEN_INPUT
        read -p "Masukkan DEVELOPER_ID: " DEVELOPER_ID_INPUT

        cat > "$BOT_PATH/.env" << END
BOT_TOKEN=$BOT_TOKEN_INPUT
DEVELOPER_ID=$DEVELOPER_ID_INPUT
ARCHIVE_DIR=arsip
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

# buat download bot.py jika belum ada
if [ ! -f "$BOT_PATH/bot.py" ]; then
    echo "📥 Mengunduh bot.py..."
    wget -q -O "$BOT_PATH/bot.py" "https://raw.githubusercontent.com/kederjider/bot-telegram/main/anonim/bot.py"
    chown "$BOT_USER:$BOT_USER" "$BOT_PATH/bot.py"
fi

# 6. Install systemd service
echo "🚀 Menginstall systemd service..."
#cp telegram-relay-bot.service /etc/systemd/system/
wget -q -O /etc/systemd/system/telegram-relay-bot.service "https://raw.githubusercontent.com/kederjider/bot-telegram/main/anonim/telegram-relay-bot.service"
systemctl daemon-reload

# 7. Enable service
echo "⚙️  Mengaktifkan service..."
systemctl enable telegram-relay-bot.service

# 8. Start service
echo "▶️  Menjalankan service..."
systemctl start telegram-relay-bot.service

# 9. Status check
echo ""
echo "✅ Instalasi selesai!"
echo ""
echo "📋 Perintah berguna:"
echo "   • Cek status:  sudo systemctl status telegram-relay-bot"
echo "   • Mulai:       sudo systemctl start telegram-relay-bot"
echo "   • Stop:        sudo systemctl stop telegram-relay-bot"
echo "   • Restart:     sudo systemctl restart telegram-relay-bot"
echo "   • Log:         sudo journalctl -u telegram-relay-bot -f"
echo ""
sleep 3
# Status service
sudo systemctl status telegram-relay-bot --no-pager
