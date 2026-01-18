import requests, os, json, time
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # 👈 NEW (IMPORTANT)

FILES = {
    "marathi": "pyq_data/marathi.txt",
    "hindi": "pyq_data/hindi.txt",
    "english": "pyq_data/english.txt"
}

STATE_FILE = "state.json"


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"index": 0}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f)


def parse_questions(text):
    blocks = text.strip().split("\n\n")
    questions = []

    for b in blocks:
        lines = b.split("\n")
        if len(lines) < 6:
            continue

        q = lines[0][3:].strip()  # Q:
        options = []
        correct = 0
        explanation = ""

        for line in lines[1:]:
            if line.startswith("E:"):
                explanation = line[2:].strip()
            elif "*" in line:
                correct = len(options)
                options.append(line[3:].replace("*", "").strip())
            else:
                options.append(line[3:].strip())

        if len(options) == 4:
            questions.append((q, options, correct, explanation))

    return questions


def send_poll(q, options, correct):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPoll"
    payload = {
        "chat_id": CHANNEL_ID,        # 👈 FIXED
        "question": q,
        "options": options,
        "type": "quiz",
        "correct_option_id": correct,
        "is_anonymous": True
    }
    r = requests.post(url, json=payload)
    return r.json()


def send_explanation(text):
    if not text:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,        # 👈 FIXED
        "text": f"📘 Explanation:\n{text}"
    }
    requests.post(url, json=payload)


# ================= MAIN =================

state = load_state()
all_q = []

for f in FILES.values():
    with open(f, "r", encoding="utf-8") as file:
        all_q.extend(parse_questions(file.read()))

start = state["index"]
end = start + 10

for q in all_q[start:end]:
    send_poll(q[0], q[1], q[2])
    time.sleep(3)
    send_explanation(q[3])
    time.sleep(3)

state["index"] = end
save_state(state)
