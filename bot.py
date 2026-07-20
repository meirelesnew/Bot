import os
import subprocess
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ["8919336807:AAE9M8wA_iZD27xTxX3jfuOAgBxRebiqktQ"]  # configurado nas variáveis de ambiente do Render/Railway
PIPER_BIN = "./piper/piper"
MODEL_PATH = "minha_voz.onnx"

async def gerar_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    saida = "saida.wav"

    # Roda o Piper: texto entra via stdin, áudio sai em arquivo
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

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, gerar_audio))

if __name__ == "__main__":
    app.run_polling()
