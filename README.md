# 🎙️ Telegram Voice TTS Bot (Piper TTS Custom Voice)

Bot do Telegram que **coleta amostras de voz** enviadas pelo usuário, permite exportar esse dataset e, com um modelo de **síntese de voz (TTS)** treinado sob medida com essa voz, responde mensagens de texto com áudios na voz clonada.

O motor de síntese é o [Piper TTS](https://github.com/rhasspy/piper), rodando em container Docker, hospedado no [Render](https://render.com) com deploy automático a cada push na branch `main`.

---

## 🏗️ Arquitetura do projeto

```
┌─────────────────────┐      ┌──────────────────────────┐      ┌────────────────────┐
│   Telegram (bot)     │      │   Treino (Kaggle/Colab)  │      │   Render (deploy)   │
│                       │      │                            │      │                      │
│  /voice → coleta      │─zip─▶│  Conversão + transcrição  │─push▶│  Docker + Piper CLI  │
│  /exportar → gera zip │      │  Fine-tuning (Piper TTS)  │      │  Responde com áudio  │
│                       │      │  Exporta .onnx + .json    │      │  na voz clonada      │
└─────────────────────┘      └──────────────────────────┘      └────────────────────┘
```

**Fluxo completo, ponta a ponta:**
1. Você manda mensagens de voz pro bot → ele salva cada uma em `/app/gravacoes`
2. Comando `/exportar` → bot devolve um `gravacoes.zip` com tudo salvo
3. Esse zip é usado no notebook de treino (Kaggle ou Colab) → conversão para `.wav`, transcrição automática (Faster-Whisper) e fine-tuning do modelo Piper
4. O notebook exporta `minha_voz.onnx` + `minha_voz.onnx.json` e faz `git push` automático direto nesse repositório
5. O Render detecta o push e redeploya o bot com a voz nova

---

## 🤖 Comandos e comportamento do bot

| Interação | O que faz |
|---|---|
| Enviar **texto** | Bot sintetiza esse texto com `minha_voz.onnx` (via Piper CLI) e responde com um áudio |
| Enviar **mensagem de voz** | Bot salva a gravação em `/app/gravacoes/gravacao_XXXX.ogg`, útil para juntar mais amostras de treino |
| `/exportar` | Zipa todas as gravações salvas e envia o arquivo `gravacoes.zip` de volta |

Arquivo principal: [`bot.py`](./bot.py) — usa `python-telegram-bot` para o bot e um servidor `Flask` mínimo em thread separada só para responder ao health check do Render.

---

## 📦 Estrutura de arquivos

```
.
├── bot.py                 # Lógica do bot (Telegram + geração de áudio)
├── Dockerfile              # Build: baixa o binário do Piper e instala dependências
├── requirements.txt        # python-telegram-bot, flask
├── minha_voz.onnx          # Modelo de voz treinado (gerado pelo pipeline de treino)
├── minha_voz.onnx.json     # Config/metadados do modelo (fonemas, sample rate etc.)
└── README.md
```

---

## 🚀 Deploy

O deploy é feito via Docker no Render, com build automático a cada push na branch `main`.

**Variáveis de ambiente necessárias no Render:**

| Variável | Descrição |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Token do bot, obtido via [@BotFather](https://t.me/BotFather) |
| `PORT` | Definida automaticamente pelo Render (usada só pro health check Flask) |

O `Dockerfile` baixa o binário oficial do Piper (`piper_linux_x86_64.tar.gz`) direto do GitHub Releases do projeto Piper na hora do build — não é necessário buildar o Piper manualmente.

---

## 🎓 Treinando uma voz nova

O modelo `.onnx` deste repositório é gerado por um pipeline separado (fora deste repo), rodado no **Kaggle Notebooks** (ou Google Colab, como alternativa) com GPU gratuita. Resumo das etapas:

1. **Coleta:** enviar mensagens de voz pro bot no Telegram, depois `/exportar` para baixar o `gravacoes.zip`
2. **Ambiente:** o notebook instala Piper TTS + PyTorch Lightning 1.9.5 (versão compatível) numa venv própria
3. **Conversão + transcrição:** os `.ogg` viram `.wav` (22050Hz mono) e são transcritos automaticamente com Faster-Whisper, gerando o `metadata.csv` no formato LJSpeech
4. **Fine-tuning:** parte do checkpoint público `rhasspy/piper-checkpoints` (voz `pt_BR/faber/medium`) e treina mais ~500 epochs sobre as amostras coletadas
5. **Exportação:** gera `minha_voz.onnx` + `minha_voz.onnx.json`
6. **Deploy automático:** o próprio notebook faz `git clone` + `git push` deste repositório com o modelo novo, usando um GitHub Token guardado como secret

**Notas importantes de quem já passou por isso (ver `progress.md` do pipeline de treino para o histórico completo de bugs corrigidos):**
- O checkpoint base já vem pré-treinado até uma epoch alta (ex.: 6159) — `max_epochs` no treino precisa ser sempre **maior** que esse valor, senão o treino recusa continuar
- Datasets pequenos (menos de ~15 amostras) tendem a gerar avisos de `audio amplitude out of range` se as gravações originais tiverem volume alto — não impede o treino, mas pode deixar a voz levemente distorcida em alguns trechos
- Se `.onnx` ultrapassar ~95MB, considerar configurar Git LFS neste repositório antes do push automático

---

## 🛠️ Rodando localmente (debug)

```bash
docker build -t muth-ai-bot .
docker run -e TELEGRAM_BOT_TOKEN=seu_token_aqui -p 10000:10000 muth-ai-bot
```

Certifique-se de que `minha_voz.onnx` e `minha_voz.onnx.json` estejam na raiz do projeto antes do build — sem eles, o comando de texto → áudio falha com "Erro ao gerar áudio 😕".
