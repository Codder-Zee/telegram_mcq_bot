import requests, os, json, time
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL")

FILES = {
    "marathi": "pyq_data/marathi.txt",
    "hindi": "pyq_data/hindi.txt",
    "english": "pyq_data/english.txt"
}

STATE_FILE = "state.json"

def load_state():
    if not os.path.exists(STATE_FILE):
        return {"index": 0}
    return json.load(open(STATE_FILE, "r", encoding="utf-8"))

def save_state(state):
    json.dump(state, open(STATE_FILE, "w", encoding="utf-8"))

def parse_questions(text):
    blocks = text.strip().split("\n\n")
    questions = []
    for b in blocks:
        lines = b.split("\n")
        q = lines[0][3:]
        options = []
        correct = 0
        explanation = ""
        for i, line in enumerate(lines[1:]):
            if line.startswith("E:"):
                explanation = line[2:].strip()
            elif "*" in line:
                correct = len(options)
                options.append(line[3:].replace("*", "").strip())
            else:
                options.append(line[3:].strip())
        questions.append((q, options, correct, explanation))
    return questions

def send_poll(q, options, correct):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPoll"
    payload = {
        "chat_id": CHANNEL,
        "question": q,
        "options": options,
        "type": "quiz",
        "correct_option_id": correct,
        "is_anonymous": True
    }
    requests.post(url, json=payload)

def send_explanation(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHANNEL, "text": f"📘 Explanation:\n{text}"})

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