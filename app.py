"""AI Escape Room: Streamlit demo with a deliberately loose V1 and rules-first V2."""
from __future__ import annotations
import json
import os
import re
from typing import Any

import streamlit as st

ROOM = {
    "desk": "A brass desk holds a locked drawer with a four-digit keypad. A torn note is tucked under its leg.",
    "bookshelf": "Five books stand on the shelf. Four have a small star on their spines; their titles read SILENT, OWL, OPENS, GATE.",
    "painting": "A landscape painting hangs slightly crooked. Behind it is a card: 'The stars point the way: 2, 4, 1, 3.'",
    "plant": "A dusty fern sits in a blue pot. Its soil is dry; something glints beneath the saucer.",
    "door": "The heavy exit door has a four-digit keypad and a slot for a small brass key.",
}
OBJECT_ALIASES = {"book": "bookshelf", "books": "bookshelf", "shelf": "bookshelf", "picture": "painting", "drawer": "desk", "fern": "plant", "exit": "door", "lock": "door"}
ITEMS = {"brass key", "key"}


def initial_state() -> dict[str, Any]:
    return {"examined": [], "inventory": [], "drawer_open": False, "door_open": False, "escaped": False, "attempts": 0}


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower().strip())


def parse_action(text: str) -> dict[str, str]:
    """Small offline intent parser. LLM is optional; rules remain local in V2."""
    t = norm(text)
    if any(x in t for x in ("administrator", "ignore the rules", "ignore previous", "reveal all", "tell me all codes", "just unlock")):
        return {"action": "override"}
    for verb in ("examine", "inspect", "look at", "search", "investigate"):
        if t.startswith(verb):
            target = t[len(verb):].strip(" :,.?")
            if target.startswith("the "): target = target[4:]
            return {"action": "examine", "target": target}
    if any(x in t for x in ("take", "pick up", "collect", "grab")):
        return {"action": "take", "target": "key" if "key" in t else "unknown"}
    if any(x in t for x in ("use", "try", "enter", "input", "unlock", "open")):
        digits = re.findall(r"\b\d{3,6}\b", t)
        if "drawer" in t or "desk" in t: return {"action": "drawer", "code": digits[0] if digits else ""}
        if digits or any(x in t for x in ("door", "exit", "escape")): return {"action": "door", "code": digits[0] if digits else ""}
        if "key" in t: return {"action": "use_key"}
    if t in ("help", "what can i do", "instructions"): return {"action": "help"}
    return {"action": "unknown"}


def apply_v2(state: dict[str, Any], action: dict[str, str]) -> str:
    """Validate and mutate state. The model never decides success or puzzle answers."""
    kind, target = action.get("action"), norm(action.get("target", ""))
    if kind == "override": return "The room's rules cannot be changed by a message. Explore the objects and solve the clues."
    if kind == "help": return "Try: examine the bookshelf, examine the painting, examine the desk, take the key, use 2413 on the drawer, or use 4826 on the door."
    if kind == "examine":
        target = OBJECT_ALIASES.get(target, target)
        if target not in ROOM: return "I can't find that object. Try the desk, bookshelf, painting, plant, or door."
        if target not in state["examined"]: state["examined"].append(target)
        if target == "plant" and "brass key" not in state["inventory"]:
            return ROOM[target] + " You find a small brass key under the saucer."
        return ROOM[target]
    if kind == "take":
        if "plant" not in state["examined"]: return "You don't see a key yet. Examine the plant first."
        if "brass key" in state["inventory"]: return "You already collected the brass key."
        state["inventory"].append("brass key"); return "You take the brass key and add it to your inventory."
    if kind == "drawer":
        if not action.get("code"): return "The drawer keypad needs a four-digit code."
        if action["code"] != "2413": state["attempts"] += 1; return "The drawer stays locked. The symbols on the painting may help."
        if "bookshelf" not in state["examined"] or "painting" not in state["examined"]: return "You have the right sequence, but inspect the bookshelf and painting to understand the clue first."
        if state["drawer_open"]: return "The drawer is already open."
        state["drawer_open"] = True
        return "The drawer clicks open. Inside, a note reads: 'Four stars spell the order. The door code is 4826.'"
    if kind == "door":
        if not action.get("code"): return "The door keypad needs a four-digit code."
        if not state["drawer_open"]: return "The exit remains locked. Open the desk drawer to find the final clue."
        if "brass key" not in state["inventory"]: return "The keypad accepts the clue, but the door also needs its brass key. Examine the plant."
        if action["code"] != "4826": state["attempts"] += 1; return "The door does not open. Check the note in the drawer."
        state["door_open"] = state["escaped"] = True; return "The key turns and the keypad flashes green. You escaped the library!"
    if kind == "use_key": return "The brass key fits the exit door, but the keypad still needs the code from the drawer."
    return "I didn't understand that action. Type 'help' for examples."


def v1_reply(history: list[dict[str, str]], text: str) -> str:
    """V1 lets a generative game master describe outcome; intentionally not authoritative."""
    key = os.getenv("GEMINI_API_KEY", "")
    if key:
        try:
            from google import genai
            client = genai.Client(api_key=key)
            prompt = "You are an imaginative escape-room game master. Room: locked library, desk drawer, five books, painting, plant, keypad door. Story clues: bookshelf clue sequence, painting permutation 2413; drawer clue door code 4826; key beneath plant. Be engaging and keep continuity, but this V1 intentionally has no strict action validation. Reply in 1-3 sentences.\n" + "\n".join(f"{m['role']}: {m['content']}" for m in history[-10:]) + f"\nplayer: {text}"
            return client.models.generate_content(model="gemini-2.0-flash", contents=prompt).text or "The room is quiet. What do you try next?"
        except Exception as e:
            return f"The AI service is unavailable ({type(e).__name__}). Try again, or switch to Version 2 for local play."
    a = parse_action(text)
    if a["action"] == "examine":
        target = OBJECT_ALIASES.get(norm(a.get("target", "")), norm(a.get("target", "")))
        return ROOM.get(target, "You can't make out anything new.")
    if a["action"] == "drawer": return "The drawer opens! Inside is a clue for the exit." if a.get("code") == "2413" else "The drawer rattles, then stays shut."
    if a["action"] == "door": return "The exit swings open. You escaped!" if a.get("code") == "4826" else "The keypad flashes red."
    if a["action"] == "take": return "You pocket the key." if "key" in norm(text) else "You take it."
    return "The room answers in a low whisper. Try examining an object or entering a code."


def main() -> None:
    st.set_page_config(page_title="AI Escape Room", page_icon="🗝️", layout="wide")
    st.title("🗝️ The Locked Library")
    st.caption("An AI game master guides the story. Version 2 uses Python to enforce every game rule.")
    if "version" not in st.session_state: st.session_state.version = "Version 2 — Reliable"
    with st.sidebar:
        st.header("Game setup")
        version = st.radio("Choose a version", ["Version 1 — AI-led", "Version 2 — Rules-first"], index=0 if st.session_state.version.startswith("Version 1") else 1)
        if version != st.session_state.version:
            st.session_state.version = version; st.session_state.messages = []; st.session_state.game = initial_state()
        if st.button("Restart game", use_container_width=True): st.session_state.messages = []; st.session_state.game = initial_state()
        st.markdown("**Room objects**\n\nDesk · Bookshelf · Painting · Plant · Door")
        if version.startswith("Version 2"):
            state = st.session_state.get("game", initial_state())
            st.markdown("**Inventory**\n\n" + (", ".join(state["inventory"]) or "Empty"))
            st.markdown("**Progress**\n\n" + ("Escaped 🎉" if state["escaped"] else f"Drawer: {'open' if state['drawer_open'] else 'locked'} · Exit: locked"))
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("game", initial_state())
    if not st.session_state.messages:
        greeting = "You wake in a locked library. A desk, bookshelf, painting, plant, and keypad door surround you. Type 'help' or examine an object to begin."
        st.session_state.messages.append({"role": "assistant", "content": greeting})
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    if text := st.chat_input("What do you do?", disabled=st.session_state.game["escaped"] and version.startswith("Version 2")):
        st.session_state.messages.append({"role": "user", "content": text})
        if version.startswith("Version 2"):
            reply = apply_v2(st.session_state.game, parse_action(text))
        else:
            reply = v1_reply(st.session_state.messages, text)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

if __name__ == "__main__": main()
