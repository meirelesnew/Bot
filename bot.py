import os
import subprocess
import logging
import threading
import zipfile
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
PIPER_BIN = "./piper/piper"
MODEL_PATH = "minha_voz.onnx"
PASTA_GRAVACOES = "/app/gravacoes"

os.makedirs(PASTA_GRAVACOES, exist_ok=True)

# --- Servidor Flask só pra responder o health check do Render ---
web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Bot rodando!"

def rodar_servidor_web():
    porta = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=porta)

# --- Gerar áudio a partir de texto (já existia) ---
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

# --- NOVO: receber e salvar mensagens de voz enviadas por você ---
async def salvar_gravacao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice
    arquivo = await context.bot.get_file(voice.file_id)

    quantidade_atual = len(os.listdir(PASTA_GRAVACOES))
    nome_arquivo = f"gravacao_{quantidade_atual + 1:04d}.ogg"
    caminho = os.path.join(PASTA_GRAVACOES, nome_arquivo)

    await arquivo.download_to_drive(caminho)

    total = len(os.listdir(PASTA_GRAVACOES))
    await update.message.reply_text(f"✅ Gravação salva ({nome_arquivo}). Total até agora: {total}")

# --- NOVO: comando /exportar - zipa tudo e devolve o arquivo ---
async def exportar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    arquivos = os.listdir(PASTA_GRAVACOES)

    if not arquivos:
        await update.message.reply_text("Nenhuma gravação encontrada ainda.")
        return

    caminho_zip = "/app/gravacoes.zip"
    with zipfile.ZipFile(caminho_zip, "w") as zipf:
        for nome in arquivos:
            zipf.write(os.path.join(PASTA_GRAVACOES, nome), arcname=nome)

    with open(caminho_zip, "rb") as z:
        await update.message.reply_document(document=z, filename="gravacoes.zip")

    os.remove(caminho_zip)

def rodar_bot():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, gerar_audio))
    app.add_handler(MessageHandler(filters.VOICE, salvar_gravacao))
    app.add_handler(CommandHandler("exportar", exportar))
    app.run_polling()

if __name__ == "__main__":
    threading.Thread(target=rodar_servidor_web, daemon=True).start()
    rodar_bot()
