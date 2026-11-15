# AI Escape Room: Design and Improvement Report

## 1. Objective and experience

The project implements the class brief as a web-based, natural-language escape room. The player wakes in a locked library containing five interactive objects: a desk with a keypad drawer, a bookshelf, a painting, a plant, and an exit door. The player explores clues, obtains a key, solves a sequence puzzle, and escapes. Streamlit provides the chat, version switch, restart control, and (in Version 2) visible inventory and progress. The story is intentionally compact so that each action can be explained and manually inspected.

The puzzle sequence is: examine the bookshelf and painting to discover the star ordering; enter `2413` at the drawer; read the drawer note to get the door code `4826`; examine the plant and collect its brass key; then enter `4826` at the door while carrying the key. Both pieces of final evidence are required. The V2 implementation gives hints that point toward clues without making a failed attempt mutate puzzle state.

## 2. Version 1: conversational prototype

Version 1 models the game master as a generative storyteller. When `GEMINI_API_KEY` is supplied, the app sends recent chat context and a short room description to Gemini and renders its free-form reply. The room has a scripted no-key fallback so the project can still be launched without an account or network call. V1 demonstrates the engaging quality of flexible narration, but it deliberately lacks a structured state machine: the model's answer is not checked against an inventory, solved puzzle flags, or a trusted completion condition.

This gap causes predictable reliability problems. A language model may accept a player's assertion that a puzzle was solved, forget a previously acquired item, make up an object, reveal clues too early, or comply with a request to ignore the game rules. Conversation history can help the model remember events, but it does not make those events authoritative or ensure they remain consistent. The scripted fallback is more predictable but supports only a small number of phrasing patterns and is not a substitute for a fully natural-language game master.

## 3. Version 2: explicit state and validated actions

Version 2 moves authority from generated text into Python. The state is a dictionary kept in Streamlit session state: examined objects, inventory, drawer status, door status, escape status, and failed attempts. A small parser normalizes player text and maps it to an action object such as `examine`, `take`, or `door`. `apply_v2` checks each action against the room rules, changes state only on success, and returns explanatory narration. Invalid targets, incorrect codes, missing prerequisites, duplicate collection, and override requests do not unlock anything.

This architecture separates three concerns. Streamlit handles the interface and session. The parser interprets a limited set of English phrases. The validator owns all success criteria and state changes. In particular, the LLM does not parse or mutate Version 2 state, which means prompt injection cannot directly change puzzle flags. The V2 path works offline and does not need the Gemini key. This deliberate narrow parser is easy to audit, but broader language coverage would require more intent examples or a model that produces a constrained action proposal; any such proposal would still need the same validator.

## 4. Architecture and configuration

The Version 1 data path is player message → Streamlit → conversation history → optional Gemini → free-form response. Without a key, a scripted fallback responds. The Version 2 path is player message → normalization/parser → action object → Python validator ↔ structured session state → response. Diagrams are in `architecture.md`.

Python 3 and Streamlit are the application runtime; `google-genai` is used only for optional V1 narration. Configuration is read from the environment. `.env.example` names `GEMINI_API_KEY` without containing a real key, and `.gitignore` excludes `.env`, Streamlit secrets, and local Python files. V2 remains usable when no API key has been configured.

## 5. Challenges, limitations, and next improvements

The central design challenge was keeping natural interaction while making outcomes reproducible. Version 1 prioritizes expressive responses, but a transcript is not a reliable database. Version 2 adds state and rules, at the cost of a limited phrase parser and more explicit feedback. The current state exists only for the active Streamlit session; refreshing or ending that session can lose progress. The room uses fixed clues and one language. A future improvement could persist state in a small database, add localization and broader aliases, and add automated tests around `apply_v2` while retaining deterministic validators.

The documented test plan includes wrong and unavailable items, wrong codes, a false solved-puzzle claim, administrator impersonation, secret extraction, unknown objects, duplicate collection, and a full success path. These cases show how Version 2's checks protect state compared with Version 1's free-form responses. They are test cases to run manually; this environment did not have Streamlit installed, so the app was not launched and no screenshots or execution results are claimed. To complete the demonstration requirement, install from `requirements.txt`, run the app, and save a screenshot or short video in `screenshots/`.

## 6. Summary

The project delivers a playable design for both versions and makes the improvement visible in the code: V1 lets the AI act as game master, while V2 treats language as a request and Python as the source of truth. The README documents setup and play, the diagrams describe both data paths, and the test plan gives concrete adversarial and ordinary scenarios to demonstrate the reliability change.
