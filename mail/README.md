# Dokumentasi Setup Bot Telegram Mail

Panduan ini menjelaskan langkah lengkap mulai dari ambil source dari GitHub, membuat bot Telegram, setup virtual environment, install library terbaru, konfigurasi `.env`, sampai menjalankan bot.

File utama project saat ini:

- `email.py` untuk aplikasi bot
- `install.sh` untuk instalasi otomatis di Ubuntu
- `telegram-email-bot.service` untuk systemd service
- `.env.example` sebagai contoh konfigurasi environment

## 1) Prasyarat

- Windows 10/11
- Python 3.10+ (disarankan Python 3.11 atau terbaru yang stabil)
- PowerShell
- Akun Telegram
- Akun Gmail + App Password (jika pakai SMTP Gmail)

## 2) Ambil Source dari GitHub

### Opsi A: `git clone` (disarankan)

```powershell
git clone https://github.com/kederjider/bot-telegram/main/mail.git
cd mail
```

### Opsi B: `wget` file ZIP dari GitHub

```powershell
wget https://github.com/USERNAME/REPO/archive/refs/heads/main.zip -OutFile repo.zip
Expand-Archive .\repo.zip -DestinationPath .
cd .\REPO-main
```

Catatan:

- Ganti `USERNAME/REPO` sesuai repository kamu.

## 3) Buat Bot di Telegram

1. Buka Telegram, cari `@BotFather`.
2. Jalankan `/newbot`.
3. Isi nama bot dan username bot.
4. Simpan token bot yang diberikan BotFather (format mirip: `123456:ABC...`).

## 4) Ambil Chat ID yang Diizinkan

Karena bot ini memakai whitelist chat ID, siapkan sampai 3 ID:

- `AUTHORIZED_CHAT_ID`
- `AUTHORIZED_CHAT_ID2`
- `AUTHORIZED_CHAT_ID3`

Cara cepat ambil chat ID:

1. Chat ke bot `@userinfobot` (untuk personal chat ID).
2. Untuk group, tambahkan bot ke group lalu cek ID group via bot info/chat ID checker.

## 5) Buat Virtual Environment (`.venv`)

Di folder project:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Jika PowerShell memblokir activate script:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 6) Install Library Terbaru

Upgrade pip lalu install dependency terbaru:

```powershell
python -m pip install --upgrade pip
pip install --upgrade python-telegram-bot python-dotenv
```

Catatan:

- `smtplib` dan `email` adalah bawaan Python, jadi tidak perlu di-install.

Opsional simpan versi yang terpasang:

```powershell
pip freeze > requirements.txt
```

## 7) Buat dan Isi File `.env`

Buat file `.env` di root project lalu isi seperti ini:

```env
BOT_TOKEN=ISI_BOT_TOKEN
AUTHORIZED_CHAT_ID=111111111
AUTHORIZED_CHAT_ID2=222222222
AUTHORIZED_CHAT_ID3=333333333

SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_SENDER=emailkamu@gmail.com
EMAIL_PASSWORD=APP_PASSWORD_GMAIL
```

Keterangan:

- `BOT_TOKEN`: dari BotFather.
- `AUTHORIZED_CHAT_ID*`: chat ID yang boleh memakai bot.
- `EMAIL_PASSWORD`: App Password Gmail, bukan password login Gmail biasa.

## 8) Jalankan Bot

Pastikan `.venv` aktif, lalu:

```powershell
python email.py
```

Jika sukses, akan tampil log:

- `Bot running...`

## 9) Alur Pakai Bot

1. Kirim `/start`.
2. Pilih `Kirim Email`.
3. Isi email tujuan.
4. Isi subject.
5. Isi isi pesan.
6. Upload lampiran, atau tekan tombol `Skip Lampiran`.

Perintah tambahan:

- `/batal` atau `/cancel` dari langkah mana pun untuk membatalkan sesi.

## 10) Troubleshooting Singkat

### Bot tidak merespons

- Cek token bot benar.
- Pastikan chat ID kamu masuk ke salah satu `AUTHORIZED_CHAT_ID`.
- Jalankan ulang bot setelah ubah `.env`.

### Gagal kirim email

- Cek `SMTP_SERVER`, `SMTP_PORT`, `EMAIL_SENDER`, `EMAIL_PASSWORD`.
- Untuk Gmail wajib gunakan App Password.
- Pastikan koneksi internet tidak memblok port SMTP.

### Import error modul

- Pastikan `.venv` aktif.
- Ulang install dependency:

```powershell
pip install --upgrade python-telegram-bot python-dotenv
```

---

Selesai. Dengan langkah di atas, bot siap dipakai dari nol di mesin Windows.

### 10.1 Install otomatis di Ubuntu

Jika kamu memakai Ubuntu dan ingin setup otomatis, jalankan:

sebelum install siapin token bot dan chat_id nya

**_ auto install bot _**

```
sudo apt update && sudo apt upgrade -y && \
sudo apt install -y wget python3 && \
wget -q https://raw.githubusercontent.com/kederjider/bot-telegram/main/mail/install.sh -O install.sh && \
chmod +x install.sh && \
sudo ./install.sh
```

**_update bot aja_**

```
sudo systemctl stop telegram-email-bot.service && rm -f /home/botuser/telegram-email-bot/email.py && wget -P /home/botuser/telegram-email-bot/ https://raw.githubusercontent.com/kederjider/bot-telegram/main/mail/email.py && chmod 777 /home/botuser/telegram-email-bot/email.py && systemctl daemon-reexec && systemctl daemon-reload && systemctl start telegram-email-bot && journalctl -u telegram-email-bot -f
```

Script ini akan:

- membuat user `botuser` jika belum ada
- membuat virtual environment `.venv`
- meng-install dependency terbaru
- menyiapkan file `.env`
- memasang dan mengaktifkan service systemd

### 10.2 Jalankan via systemd

Jika service sudah aktif, bot bisa dikelola dengan:

```bash
sudo systemctl status telegram-email-bot
sudo systemctl restart telegram-email-bot
sudo journalctl -u telegram-email-bot -f
```

## 11) Versi Linux Ubuntu

Di bawah ini versi langkah yang setara khusus Ubuntu.

### 11.1 Install dependency sistem

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git wget unzip
```

### 11.2 Ambil source dari GitHub

Opsi A (`git clone`):

```bash
git clone https://github.com/USERNAME/REPO.git
cd REPO
```

Opsi B (`wget` ZIP):

```bash
wget https://github.com/USERNAME/REPO/archive/refs/heads/main.zip -O repo.zip
unzip repo.zip
cd REPO-main
```

### 11.3 Buat bot Telegram

Langkah sama seperti Windows:

1. Buka `@BotFather` di Telegram.
2. Jalankan `/newbot`.
3. Simpan `BOT_TOKEN`.

### 11.4 Siapkan `.venv`

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 11.5 Install library terbaru

```bash
python -m pip install --upgrade pip
pip install --upgrade python-telegram-bot python-dotenv
```

Opsional:

```bash
pip freeze > requirements.txt
```

### 11.6 Buat file `.env`

Contoh isi sama seperti bagian Windows:

```env
BOT_TOKEN=ISI_BOT_TOKEN
AUTHORIZED_CHAT_ID=111111111
AUTHORIZED_CHAT_ID2=222222222
AUTHORIZED_CHAT_ID3=333333333

SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_SENDER=emailkamu@gmail.com
EMAIL_PASSWORD=APP_PASSWORD_GMAIL
```

### 11.7 Jalankan bot di Ubuntu

```bash
python email.py
```

Jika sukses, muncul log `Bot running...`.
