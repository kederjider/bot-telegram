# 🤖 Telegram Relay Bot - Setup & Deployment

Bot relay Telegram untuk meneruskan pesan user ke developer dengan arsip otomatis.

## 📋 Daftar Isi

1. [Instalasi Lokal](#instalasi-lokal)
2. [Setup Konfigurasi .env](#setup-konfigurasi-env)
3. [Instalasi Systemd Service (Linux/Ubuntu)](#instalasi-systemd-service)
4. [Troubleshooting](#troubleshooting)

---

## 🏠 Instalasi Lokal

### Prasyarat

- Python 3.8+
- pip atau venv

### Langkah Instalasi

1. **Buat virtual environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # atau
   venv\Scripts\activate  # Windows
   ```

2. **Install dependencies:**

   ```bash
   pip install --upgrade pip
   pip install python-telegram-bot python-dotenv
   ```

3. **Setup file .env** (lihat bagian [Setup Konfigurasi](#setup-konfigurasi-env))

4. **Jalankan bot:**
   ```bash
   python bot.py
   ```

---

## 🔑 Setup Konfigurasi .env

### 1. Buat file .env

Salin template dari `.env.example`:

```bash
cp .env.example .env
```

### 2. Edit file .env

Buka file `.env` dan isi konfigurasi:

```env
# Token bot dari @BotFather (https://t.me/botfather)
BOT_TOKEN=123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh

# Chat ID developer (penerima pesan)
# Dapatkan dari @userinfobot
DEVELOPER_ID=987654321

# Folder penyimpanan arsip (opsional)
ARCHIVE_DIR=arsip
```

### 3. Dapatkan Token dari @BotFather

1. Buka [@BotFather](https://t.me/botfather) di Telegram
2. Kirim `/newbot`
3. Ikuti instruksi untuk membuat bot
4. Copy token yang diberikan

### 4. Dapatkan DEVELOPER_ID

**Opsi A: Dari @userinfobot**

1. Buka [@userinfobot](https://t.me/userinfobot)
2. Bot akan mengirim User ID Anda
3. Copy ID tersebut ke DEVELOPER_ID

**Opsi B: Dari Logging (saat bot berjalan)**

1. Jalankan bot: `python bot.py`
2. Kirim pesan apapun ke bot
3. Cek log untuk melihat user_id Anda
4. Copy ke DEVELOPER_ID di .env

---

## 🚀 Instalasi Systemd Service (Linux/Ubuntu)

Buat bot berjalan otomatis di background bahkan setelah reboot server.

### Prasyarat

- Server Linux (Ubuntu, Debian, CentOS, dll)
- Akses sudo/root
- Bot di directory `/home/botuser/telegram-relay-bot`

### Instalasi Otomatis (Recommended)

1. **Download script instalasi:**

   ```bash
   sudo bash install_service.sh
   ```

   Script ini akan:
   - ✅ Membuat user `botuser`
   - ✅ Setup Python virtual environment
   - ✅ Install semua dependencies
   - ✅ Register systemd service
   - ✅ Auto-start on boot

### Instalasi Manual

Jika Anda lebih suka melakukan secara manual:

1. **Buat user bot:**

   ```bash
   sudo useradd -m -s /bin/bash botuser
   ```

2. **Setup directory:**

   ```bash
   sudo mkdir -p /home/botuser/telegram-relay-bot
   sudo cp -r ./* /home/botuser/telegram-relay-bot/
   sudo chown -R botuser:botuser /home/botuser/telegram-relay-bot
   ```

3. **Setup virtual environment:**

   ```bash
   cd /home/botuser/telegram-relay-bot
   sudo -u botuser python3 -m venv venv
   sudo -u botuser venv/bin/pip install python-telegram-bot python-dotenv
   ```

4. **Copy service file:**

   ```bash
   sudo cp telegram-relay-bot.service /etc/systemd/system/
   sudo systemctl daemon-reload
   ```

5. **Enable & start service:**

   ```bash
   sudo systemctl enable telegram-relay-bot.service
   sudo systemctl start telegram-relay-bot.service
   ```

6. **Cek status:**
   ```bash
   sudo systemctl status telegram-relay-bot
   ```

---

## 📊 Manajemen Service

### Perintah Dasar

```bash
# Cek status service
sudo systemctl status telegram-relay-bot

# Mulai service
sudo systemctl start telegram-relay-bot

# Stop service
sudo systemctl stop telegram-relay-bot

# Restart service
sudo systemctl restart telegram-relay-bot

# Enable auto-start on boot
sudo systemctl enable telegram-relay-bot

# Disable auto-start
sudo systemctl disable telegram-relay-bot
```

### Melihat Log

```bash
# Real-time log (last 50 lines)
sudo journalctl -u telegram-relay-bot -n 50 -f

# Log dari waktu tertentu
sudo journalctl -u telegram-relay-bot --since "1 hour ago"

# All logs
sudo journalctl -u telegram-relay-bot
```

---

## 🔒 Keamanan

⚠️ **PENTING: Lindungi file .env Anda**

### .gitignore sudah dikonfigurasi untuk:

- ❌ Jangan commit `.env` (berisi kredensial sensitif)
- ✅ Commit `.env.example` (sebagai template)
- ❌ Jangan commit folder `arsip/`

### Best Practices:

1. **Jangan commit `.env`** ke Git/GitHub
2. **Gunakan `.env.example`** untuk dokumentasi konfigurasi
3. **Backup .env** di tempat aman
4. **Rotate token** jika terjadi security breach
5. **Gunakan file permissions:** `chmod 600 .env`

---

## 🐛 Troubleshooting

### Bot tidak berjalan setelah reboot

```bash
# Cek apakah service enabled
sudo systemctl is-enabled telegram-relay-bot

# Enable jika belum
sudo systemctl enable telegram-relay-bot

# Restart service
sudo systemctl restart telegram-relay-bot
```

### Error: BOT_TOKEN tidak ditemukan

```
Solusi:
1. Pastikan file .env ada di directory yang sama dengan bot.py
2. Cek isi .env file tidak kosong
3. Pastikan tidak ada spasi di awal/akhir token
```

### Error: DEVELOPER_ID tidak valid

```
Solusi:
1. Pastikan DEVELOPER_ID adalah angka (bukan string)
2. Dapatkan ID dari @userinfobot
3. Restart bot setelah update .env
```

### Service tidak start otomatis setelah reboot

```bash
# Cek log untuk error
sudo journalctl -u telegram-relay-bot --since "1 hour ago"

# Cek file paths di service file
sudo nano /etc/systemd/system/telegram-relay-bot.service

# Reload systemd daemon
sudo systemctl daemon-reload

# Restart service
sudo systemctl restart telegram-relay-bot
```

### Permissions error

```bash
# Fix permisi direktori
sudo chown -R botuser:botuser /home/botuser/telegram-relay-bot
sudo chmod 755 /home/botuser/telegram-relay-bot
sudo chmod 600 /home/botuser/telegram-relay-bot/.env
```

---

## 📚 Fitur Bot

### Pesan dari User → Developer

- 💬 Teks
- 🖼️ Foto
- 🎬 Video
- 🎵 Audio/MP3
- 🎙️ Voice Note
- 📄 Dokumen
- 🎭 Stiker

Semua tersimpan di folder `arsip/<user_id>/`

### Perintah Developer

**Text Reply:**

```
/reply <user_id> <pesan teks>
Contoh: /reply 123456789 Halo, ini balasan dari developer!
```

**Media Reply:**

```
/send_to <user_id> + lampirkan media
Contoh: /send_to 123456789 (+ kirim foto)
```

**List Users:**

```
/users
Menampilkan daftar semua user yang pernah menghubungi
```

**History Chat:**

```
/history <user_id>
Menampilkan 20 pesan terakhir dengan user tertentu
```

---

## 📝 File Structure

```
telegram-relay-bot/
├── bot.py                          # Main script
├── .env                            # Konfigurasi (⚠️ jangan commit)
├── .env.example                    # Template konfigurasi
├── .gitignore                      # Git ignore rules
├── telegram-relay-bot.service      # Systemd service file
├── install_service.sh              # Instalasi otomatis script
├── README.md                       # Dokumentasi ini
└── arsip/                          # Folder penyimpanan arsip
    ├── <user_id1>/
    │   ├── log.json
    │   └── media/
    └── <user_id2>/
        ├── log.json
        └── media/
```

---

## 🔄 Update Bot

Setelah membuat perubahan pada script:

```bash
# Stop service
sudo systemctl stop telegram-relay-bot

# Update file (jika di /home/botuser/telegram-relay-bot)
sudo cp bot.py /home/botuser/telegram-relay-bot/

# Restart service
sudo systemctl start telegram-relay-bot

# Cek log
sudo journalctl -u telegram-relay-bot -f
```

---

## 📞 Support

Jika ada masalah, cek:

1. ✅ File .env ada dan terisi dengan benar
2. ✅ BOT_TOKEN valid dari @BotFather
3. ✅ DEVELOPER_ID benar (angka saja)
4. ✅ Dependencies terinstall: `pip list | grep python-telegram-bot`
5. ✅ Log terakhir: `sudo journalctl -u telegram-relay-bot -n 20`

---

**Happy Botting! 🚀**
