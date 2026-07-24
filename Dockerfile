FROM python:3.11-slim

WORKDIR /app

# Baixa e instala o executável do Piper
RUN apt-get update && apt-get install -y wget tar && \
    wget https://github.com/rhasspy/piper/releases/latest/download/piper_linux_x86_64.tar.gz && \
    tar -xzf piper_linux_x86_64.tar.gz && \
    rm piper_linux_x86_64.tar.gz && \
    apt-get remove -y wget && apt-get autoremove -y

# Instala as dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código e os arquivos .onnx e .json da sua voz para o container
COPY . .

# Inicia o bot
CMD ["python", "bot.py"]
