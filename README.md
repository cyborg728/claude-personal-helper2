# Telegram Personal Helper Bot

Telegram bot with AI-powered translation features using Google Gemini. Supports both polling and webhook modes.

## Features

- **AI Translation** — Automatically translates business messages via Google Gemini
- **Voice Transcription** — Transcribes and translates voice messages
- **Multi-language** — Localization in English, Russian, Korean (fluent)
- **Access Control** — Admin whitelist management
- **Translation Whitelist** — Fine-grained control over who gets translated
- **Dual Mode** — Polling for development, webhook for production

## Environment Variables

| Variable | Description | Required |
|---|---|---|
| `BOT_TELEGRAM_TOKEN` | Telegram Bot API token | Yes |
| `BOT_ADMIN_USERNAME` | Admin username (without @) | Yes |
| `BOT_GEMINI_API_KEY` | Google Gemini API key | Yes |
| `BOT_GEMINI_MODEL` | Gemini model name | No (default: `gemini-2.5-flash`) |
| `BOT_MODE` | `polling` or `webhook` | No (default: `polling`) |
| `BOT_WEBHOOK_DOMAIN` | Webhook domain | No (default: `tg-assistant.f-f.dev`) |
| `BOT_DATABASE_URL` | SQLite connection string | No (default: `sqlite+aiosqlite:///data/bot.db`) |

## Local Development

```bash
pip install -e .
BOT_TELEGRAM_TOKEN=... BOT_ADMIN_USERNAME=... BOT_GEMINI_API_KEY=... python -m bot.app
```

---

## Deployment to Kubernetes (k3s)

### 1. Add imagePullSecret for private GitHub Container Registry

Create a GitHub Personal Access Token (PAT) with `read:packages` scope, then create the secret:

```bash
kubectl create namespace telegram-bot

kubectl create secret docker-registry ghcr-secret \
  --namespace=telegram-bot \
  --docker-server=ghcr.io \
  --docker-username=YOUR_GITHUB_USERNAME \
  --docker-password=YOUR_GITHUB_PAT \
  --docker-email=YOUR_EMAIL
```

### 2. Create bot secrets

```bash
kubectl create secret generic telegram-bot-secrets \
  --namespace=telegram-bot \
  --from-literal=BOT_TELEGRAM_TOKEN=your-telegram-token \
  --from-literal=BOT_ADMIN_USERNAME=your-admin-username \
  --from-literal=BOT_GEMINI_API_KEY=your-gemini-api-key \
  --from-literal=BOT_GEMINI_MODEL=gemini-2.5-flash
```

### 3a. Deploy in WEBHOOK mode

Webhook mode requires an Ingress controller and TLS (cert-manager recommended).

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/deployment-webhook.yaml
```

The bot will be available at `https://tg-assistant.f-f.dev/webhook`.

### 3b. Deploy in POLLING mode

Polling mode does not require Ingress or TLS. Simpler setup.

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/deployment-polling.yaml
```

### 4. Verify deployment

```bash
kubectl get pods -n telegram-bot
kubectl logs -n telegram-bot -l app=telegram-bot -f
```

## Bot Commands

- `/start` — Welcome message
- `/whitelist` — Manage user access (admin only)
- `/translator` — Translation settings (admin only)

## Architecture

```
bot/
├── app.py              # Entry point (polling/webhook)
├── settings.py         # Pydantic settings
├── database.py         # SQLAlchemy async engine
├── models.py           # SQLModel models
├── webhook.py          # Litestar webhook server
├── handlers/
│   ├── start.py        # /start command
│   ├── whitelist.py    # /whitelist command + inline menu
│   ├── translator.py   # /translator command + inline menu
│   └── business.py     # Business message translation
├── services/
│   ├── gemini.py       # Google Gemini API client
│   └── localization.py # Fluent localization
├── middleware/
│   └── access.py       # Access control checks
└── locales/
    ├── en/main.ftl
    ├── ru/main.ftl
    └── ko/main.ftl
```
