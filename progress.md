# Progress — Pipeline de Voz Clonada (Piper TTS) → Bot "Muth AI" no Telegram

## Visão geral do projeto

**Objetivo:** treinar uma voz clonada em português (fine-tuning sobre o checkpoint
`pt_BR/faber/medium` do Piper), usando gravações reais baixadas do Telegram, e
publicar o modelo treinado (`.onnx`) direto no repositório do bot para que o
Render redeploye automaticamente.

**Stack:**
- Treino: Piper TTS (`piper_train`) + PyTorch Lightning 1.9.5 + Kaggle Notebooks (GPU)
- Transcrição automática dos áudios: Faster-Whisper (modelo `medium`, pt)
- Conversão de áudio: pydub (`.ogg` → `.wav` 22050Hz mono)
- Deploy: `git push` automatizado via token do GitHub, direto do notebook
- Bot: repositório `github.com/meirelesnew/Bot`, hospedado no Render
  (redeploy automático a cada push na branch `main`)

**Arquivo principal do pipeline:** `treinar_voz_piper_kaggle.py`
(versão adaptada do Colab para rodar no Kaggle — ver seção "Migração Colab → Kaggle")

---

## ✅ Problemas já corrigidos

### 1. Tela em branco durante o treino (falso "travamento")
- **Causa:** `subprocess.run(..., capture_output=True)` só imprime a saída depois
  que o processo inteiro termina. Como o treino pode levar horas, a tela ficava
  em branco e parecia travado.
- **Fix:** criada `rodar_com_stream()`, usando `subprocess.Popen` com
  `stdout=subprocess.PIPE` e leitura linha a linha em tempo real.

### 2. `FileNotFoundError` no treino (Kaggle e Colab)
- **Causa:** a chamada de `rodar_com_stream()` para o comando de treino não
  passava `shell=True`. Sem isso, o `subprocess.Popen` tentou interpretar a
  string inteira do comando como o nome de um único executável.
- **Fix:** adicionado `shell=True` na chamada.

### 3. `MisconfigurationException`: checkpoint com epoch maior que `max_epochs`
- **Causa:** o checkpoint base `pt_BR/faber/medium` já vem pré-treinado até uma
  epoch alta (ex.: 6159). `max_epochs` no Lightning é um **teto absoluto**, não
  "epochs adicionais" — setar um valor menor que a epoch do checkpoint trava o
  treino.
- **Fix:** `max_epochs` calculado dinamicamente como
  `epoch_inicial_do_checkpoint + epochs_adicionais_de_fine_tuning` (hoje: 6159 + 500 = 6659).
- **⚠️ Atenção:** o número da epoch inicial do checkpoint pode mudar se o
  Hugging Face atualizar o arquivo. O script imprime o nome do checkpoint
  baixado (`caminho_relativo`) antes de treinar — sempre conferir esse valor.

### 4. `IndexError: list index out of range` na exportação do `.onnx`
- **Causa:** o glob de busca de checkpoints procurava só em `version_0/checkpoints/`.
  Em execuções repetidas, o Lightning cria pastas `version_1`, `version_2` etc.,
  e `version_0` ficava vazia.
- **Fix:** glob trocado para `version_*/checkpoints/*.ckpt` (busca em todas as
  versões), ordenado por `os.path.getmtime` (data de modificação real, não nome).

### 5. Migração Colab → Kaggle (cota de GPU do Colab esgotada)
Trocas feitas para rodar em `treinar_voz_piper_kaggle.py`:

| Item | Colab | Kaggle |
|---|---|---|
| Pasta base | `/content/` | `/kaggle/working/` |
| Upload de áudio | `google.colab.files.upload()` (widget que só funciona no Colab) | Dataset subido manualmente via **Add Input → Upload**, lido de `/kaggle/input/` |
| Token do GitHub | `google.colab.userdata` | `kaggle_secrets.UserSecretsClient()` |
| Download do `.onnx` | `files.download()` | Não precisa — vai direto pro GitHub via Célula 5 |

### 6. Zip não encontrado no Kaggle
- **Causa:** o Kaggle **extrai automaticamente** arquivos `.zip` ao criar um
  dataset — não sobra nenhum `.zip` dentro de `/kaggle/input/`, só os arquivos
  `.ogg` soltos.
- **Fix:** script agora procura primeiro por `.ogg` direto (`glob` recursivo);
  só tenta extrair `.zip` como fallback, caso um dia o comportamento do Kaggle mude.

---

## 🎉 Execução que funcionou de ponta a ponta (25/07/2026)

- Dataset: 13 áudios (`meuaudio` no Kaggle)
- Treino: epoch 6159 → 6659 (500 epochs de fine-tuning), sem erros
- Modelo exportado: `minha_voz.onnx`, **60.6 MB**
- Push automático: commit `7bca5c1` em `meirelesnew/Bot`, branch `main`
- Deploy: Render deve redeployar automaticamente a partir do push

---

## ⏳ Pendências / pontos de atenção

### 1. Clipping de áudio nas gravações originais (não bloqueante)
Durante o treino, apareceram repetidos avisos:
```
warning: audio amplitude out of range, auto clipped.
```
Isso indica que algumas das 13 gravações originais têm volume gravado alto
demais (estourando a amplitude). Não impede o treino, mas pode deixar a voz
sintetizada com leve distorção em trechos parecidos com essas amostras.

**Ação sugerida (se a qualidade da voz não agradar):** regravar essas amostras
com volume mais controlado e rodar o pipeline de novo. Dataset maior (30min+
de fala variada) também tende a melhorar a naturalidade — hoje são só 13
frases curtas.

### 2. `HF_TOKEN` não configurado (opcional)
Downloads do Hugging Face Hub aparecem com aviso de "unauthenticated requests"
— funciona normalmente, mas com rate limit mais baixo. Só relevante se for
rodar múltiplos treinos seguidos no mesmo dia.
Fix opcional: criar secret `HF_TOKEN` no Kaggle (Add-ons → Secrets) e usar
`os.environ["HF_TOKEN"] = user_secrets.get_secret("HF_TOKEN")` antes do
`hf_hub_download`.

### 3. Confirmar teste real do bot no Telegram
Push feito e Render deve ter redeployado — falta validar na prática se o
bot gera áudio corretamente agora (sem o erro "Erro ao gerar áudio" visto
antes do primeiro modelo publicado).

### 4. `EPOCH_INICIAL_DO_CHECKPOINT` fixo no código (débito técnico leve)
Hoje hardcoded como `6159`. Se o checkpoint do Hugging Face mudar no futuro,
essa constante vai ficar desatualizada e pode reintroduzir o erro do item 3
da lista de correções. Melhoria futura: extrair o número da epoch
automaticamente do nome do arquivo (`caminho_relativo`) via regex, em vez de
exigir ajuste manual.

---

## Comandos/valores de referência

- Repo do bot: `https://github.com/meirelesnew/Bot.git`
- Branch de deploy: `main`
- Checkpoint base: `rhasspy/piper-checkpoints` → `pt/pt_BR/faber/medium/*.ckpt`
- Batch size usado: `6` (ajustado de 12 para evitar OOM em GPU T4)
- Epochs de fine-tuning por rodada: `+500` sobre a epoch do checkpoint
- Secrets necessários: `GITHUB_TOKEN` (obrigatório), `HF_TOKEN` (opcional)
