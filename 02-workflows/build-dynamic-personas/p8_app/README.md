# Role-Play App (Phase 8)

Local web app for running a five-persona focus-group conversation.

## 1) Install dependencies

```bash
cd "/Users/david/Library/CloudStorage/GoogleDrive-david.hawdale@hawdale-associates.co.uk/Shared drives/HA Shared GDrive 4TB/Claude/dynamic-personas-from-data"
python3 -m pip install -r 02-workflows/build-dynamic-personas/p8_app/requirements.txt
```

## 2) Set OpenAI API key

```bash
set -a
source .env
set +a
```

Or set directly:

```bash
export OPENAI_API_KEY="your_key_here"
```

## 3) Prepare role-play pack

```bash
python3 02-workflows/build-dynamic-personas/prepare-roleplay-pack.py
python3 02-workflows/build-dynamic-personas/verify-roleplay-pack.py
```

## 4) Start the app

```bash
python3 02-workflows/build-dynamic-personas/run-roleplay-app.py
```

Open in browser:

- `http://127.0.0.1:8016`

## 5) Use it

1. Click **Create New Session**
2. Enter a question
3. Click **Ask Panel**
4. Ask follow-up questions in the same session to continue the conversation

## Stop the app

In the terminal running it, press `Ctrl + C`.
