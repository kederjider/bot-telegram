#!/bin/bash
# Quick Setup Script untuk Development
# Jalankan: bash quick_setup.sh

echo "🚀 Telegram Relay Bot - Quick Setup"
echo "═══════════════════════════════════"
echo ""

# 1. Create virtual env
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# 2. Activate venv
echo "✅ Activating virtual environment..."
source venv/bin/activate 2>/dev/null || . venv/Scripts/activate 2>/dev/null

# 3. Install dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

# 4. Create .env if not exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file and fill in:"
    echo "   - BOT_TOKEN: dari @BotFather"
    echo "   - DEVELOPER_ID: ID Anda (dari @userinfobot)"
    echo ""
fi

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your BOT_TOKEN and DEVELOPER_ID"
echo "2. Run bot: python bot.py"
echo ""
echo "For server deployment with systemd:"
echo "   See SETUP_GUIDE.md"
