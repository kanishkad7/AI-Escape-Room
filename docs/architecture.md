# Architecture

## Version 1 — AI-led

```mermaid
flowchart LR
    P[Player message] --> UI[Streamlit chat]
    UI --> H[Conversation history]
    H --> GM[Gemini game master, optional]
    GM --> R[Free-form reply]
    R --> UI
    F[Scripted fallback, no key] --> R
```

Conversation text provides continuity, but there is no structured game state or authoritative check. When Gemini is configured, it decides what happened in its reply. The fallback supports a few common actions only.

## Version 2 — Rules-first

```mermaid
flowchart LR
    P[Player message] --> UI[Streamlit chat]
    UI --> N[Normalize and parse intent]
    N --> A[Action object]
    A --> V[Python rule validator]
    V <--> S[Structured session state]
    V --> R[Outcome and narration]
    R --> UI
```

Python owns puzzle answers, inventory, prerequisites, and completion. No model can directly write state. Invalid actions return feedback without corrupting progress; the state lives in the Streamlit session.
