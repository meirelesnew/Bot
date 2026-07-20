FROM python:3.11-slim

WORKDIR /app

# Baixa o Piper (binário linux x86_64, compatível com Render/Railway)
RUN apt-get update && apt-get install -y wget tar && \
    wget https://github.com/rhasspy/piper/releases/latest/download/piper_linux_x86_64.tar.gz && \
    tar -xzf piper_linux_x86_64.tar.gz && \
    rm piper_linux_x86_64.tar.gz && \
    apt-get remove -y wget && apt-get autoremove -y

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
