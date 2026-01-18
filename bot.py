import requests, os, json, hashlib

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

FILE = "pyq_data/marathi.txt"
STATE_FILE = "state.json"


def load_state():
    if not os.path.exists(STATE_FILE):
        return {"used": []}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def hash_q(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def parse_questions(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    questions = []

    i = 0
    while i < len(lines):
        z_line = ""
        if lines[i].startswith("Z:"):
            z_line = lines[i][2:].strip()
            i += 1

        if not lines[i].startswith("Q:"):
            i += 1
            continue

        q = lines[i][2:].strip()
        i += 1

        options = []
        correct = 0

        for _ in range(4):
            line = lines[i]
            if "*" in line:
                correct = len(options)
                options.append(line[3:].replace("*", "").strip())
            else:
                options.append(line[3:].strip())
            i += 1

        if len(options) == 4:
            if z_line:
                q = f"[{z_line}]\n\u200b\n Q: {q}"
            else:
                q = f"Q: {q}"

            questions.append((q, options, correct))

    return questions


def send_poll(q, options, correct):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPoll"
    payload = {
        "chat_id": CHANNEL_ID,
        "question": q,
        "options": options,
        "type": "quiz",
        "correct_option_id": correct,
        "is_anonymous": True
    }
    r = requests.post(url, json=payload)
    print(r.text)


# ================= MAIN =================

state = load_state()

with open(FILE, "r", encoding="utf-8") as f:
    questions = parse_questions(f.read())

print("TOTAL QUESTIONS:", len(questions))

for q in questions:
    h = hash_q(q[0])
    if h in state["used"]:
        continue

    send_poll(q[0], q[1], q[2])
    state["used"].append(h)
    save_state(state)
    break   # हर run में सिर्फ 1 नया question
