# AI Escape Room

A small Streamlit escape-room game with two selectable implementations. Version 1 uses an AI-led game master (Gemini optional) and intentionally demonstrates how free-form model decisions can drift. Version 2 validates actions and puzzle outcomes in Python; the model is not the authority over game state. It needs no API key and has an offline command parser.

## Requirements

- Python 3.10 or newer
- Internet access and a Gemini API key only if you want generative narration in Version 1

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

This installs the app and runs it in offline mode. To add Gemini narration to Version 1, install optional dependencies with `pip install -r requirements-ai.txt`, then set `GEMINI_API_KEY` in your shell before starting Streamlit. On macOS/Linux, use `export GEMINI_API_KEY="your-key"`; on Windows PowerShell, use `$env:GEMINI_API_KEY="your-key"`. Without the key, Version 1 uses a small scripted fallback and Version 2 remains fully playable offline. Do not commit credentials. Restarting the game clears the session state.

## How to play

Send natural-language actions in the chat. Start with `examine the bookshelf`, `examine the painting`, `examine the plant`, then `take the key`. The bookshelf and painting reveal how to get the drawer code (2413); the drawer note reveals the exit code (4826). The key beneath the plant is also required to leave. Version 2 accepts aliases and shows inventory/progress in the sidebar. Type `help` for examples.

## Versions and design

- **V1 — AI-led:** a generative game master responds to the conversation. State is the conversation transcript, with no authoritative validator. The no-key fallback is intentionally minimal. It can claim success without checking prerequisites.
- **V2 — Rules-first:** an explicit state dictionary stores examined objects, inventory, drawer/door status, attempts, and completion. A parser maps text to actions; `apply_v2` checks prerequisites and mutates state. The Gemini key is not used in V2. The narration and parser can be replaced without granting them authority to unlock anything.

See [design report](docs/design-report.md), [test cases](docs/test-cases.md), and [architecture diagrams](docs/architecture.md). The test cases are a proposed manual test plan and have not been executed in this environment. Run the app and capture a screenshot or short screen recording for submission in `screenshots/`.

## Project structure

```text
app.py                 Streamlit UI, V1 game master, V2 parser and rules
requirements.txt       Core runtime dependencies
requirements-ai.txt   Optional Gemini integration
.env.example           Optional Gemini key name (no real secret)
docs/                  Architecture, test plan, design report
screenshots/           Capture a running app here before submission
```

## Known limitations

The offline parser supports a deliberately small set of English action phrases. V1 may invent or contradict room details when backed by an LLM; it is included as a comparison, not as the safe implementation. V2 uses a fixed puzzle and in-memory Streamlit session state, so progress is lost when a session ends or the app restarts. There is no user account, persistence database, or multiplayer support.
