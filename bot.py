import os
import subprocess
import logging
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
PIPER_BIN = "./piper/piper"
MODEL_PATH = "minha_voz.onnx"

# --- Servidor Flask só pra responder o health check do Render ---
web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Bot rodando!"

def rodar_servidor_web():
    porta = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=porta)

# --- Lógica do bot do Telegram (igual antes) ---
async def gerar_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    saida = "saida.wav"

    processo = subprocess.run(
        [PIPER_BIN, "-m", MODEL_PATH, "-f", saida],
        input=texto.encode("utf-8"),
        capture_output=True
    )

    if processo.returncode != 0:
        await update.message.reply_text("Erro ao gerar áudio 😕")
        logging.error(processo.stderr.decode())
        return

    with open(saida, "rb") as audio:
        await update.message.reply_voice(voice=audio)

    os.remove(saida)

def rodar_bot():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, gerar_audio))
    app.run_polling()

if __name__ == "__main__":
    # Roda o servidor web numa thread separada, e o bot na principal
    threading.Thread(target=rodar_servidor_web, daemon=True).start()
    rodar_bot()
