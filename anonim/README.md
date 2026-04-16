# 🤖 Telegram Relay Bot

Bot ini berfungsi sebagai **pihak ketiga** antara user dan developer.
Semua pesan dari user otomatis diteruskan ke developer, dan developer bisa membalas langsung ke user.

---

## 📦 Instalasi

sebelum install siapin token bot dan chat_id nya

**_ auto install bot _**

```
apt update && apt upgrade -y && apt install wget && apt install python && wget -q https://raw.githubusercontent.com/kederjider/bot-telegram/main/anonim/install_service.sh && chmod +x install_service.sh && ./install_service.sh
```

## ⚙️ Konfigurasi

Buka `.env` dan isi 2 variabel ini di bagian atas file:

```python
BOT_TOKEN    = "TOKEN_BOT_ANDA"   # Dapatkan dari @BotFather di Telegram
DEVELOPER_ID = 123456789           # Chat ID Anda sebagai developer
```

**Cara mendapatkan Chat ID Anda:**

1. Kirim pesan ke @userinfobot di Telegram
2. Atau jalankan bot dulu, lalu cek log terminal saat Anda `/start`

---

## ▶️ Menjalankan Bot

```bash
python bot.py
```

---

## 📋 Fitur

### Dari Sisi User

User cukup kirim pesan biasa ke bot — semua jenis pesan didukung:
| Jenis | Keterangan |
|-------|-----------|
| 💬 Teks | Pesan teks biasa |
| 🖼️ Foto | Gambar/foto |
| 🎬 Video | File video |
| 🎵 Audio/MP3 | File musik |
| 🎙️ Voice Note | Rekaman suara |
| 📄 Dokumen | File apapun |
| 🎭 Stiker | Stiker Telegram |

Setelah mengirim, user mendapat konfirmasi: _"✅ Pesan Anda telah diterima"_

---

### Dari Sisi Developer

Developer menerima semua pesan beserta info lengkap user (nama, username, ID).

**Perintah yang tersedia:**

#### `/reply <user_id> <pesan>`

Balas pesan teks ke user tertentu.

```
/reply 987654321 Halo! Terima kasih sudah menghubungi kami.
```

#### `/send_to <user_id>` + lampiran media

Kirim foto, video, audio, voice, atau dokumen ke user.
Caranya: ketik `/send_to 987654321` di caption saat mengirim media.

#### `/users`

Lihat daftar semua user yang pernah menghubungi bot, beserta jumlah pesan dan waktu terakhir.

#### `/history <user_id>`

Lihat 20 riwayat percakapan terakhir dengan user tertentu.

```
/history 987654321
```

---

## 🗂️ Struktur Arsip

Semua pesan dan media disimpan otomatis di folder `arsip/`:

```
arsip/
├── 987654321/           ← folder per user (berdasarkan ID)
│   ├── log.json         ← riwayat semua percakapan (JSON)
│   └── media/
│       ├── 987654321_20240101_120000_photo.jpg
│       ├── 987654321_20240101_121500_video.mp4
│       └── ...
└── 111222333/
    ├── log.json
    └── media/
```

**Contoh isi `log.json`:**

```json
[
  {
    "timestamp": "2024-01-01T12:00:00",
    "direction": "user→dev",
    "type": "text",
    "content": "Halo, saya butuh bantuan",
    "file_path": ""
  },
  {
    "timestamp": "2024-01-01T12:05:00",
    "direction": "dev→user",
    "type": "text",
    "content": "Halo! Ada yang bisa kami bantu?",
    "file_path": ""
  }
]
```

---

## 🔒 Keamanan

- Hanya `DEVELOPER_ID` yang bisa menggunakan perintah `/reply`, `/send_to`, `/users`, `/history`
- User biasa tidak bisa mengakses perintah developer
- Semua media diunduh dan disimpan lokal sebagai backup

---

## 📝 Catatan

- Bot menggunakan `python-telegram-bot` versi 21.x (async)
- Jalankan dengan Python 3.9+
- Untuk produksi, pertimbangkan menggunakan `systemd` atau `supervisor` agar bot berjalan terus
