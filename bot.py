import requests, os, json, time, hashlib

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


def hash_question(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def parse_questions(text):
    blocks = text.strip().split("\n\n")
    questions = []

    for b in blocks:
        lines = b.strip().split("\n")

        z_line = ""
        if lines[0].startswith("Z:"):
            z_line = lines[0][2:].strip()
            lines = lines[1:]

        if not lines[0].startswith("Q:"):
            continue

        q_text = lines[0][2:].strip()
        options = []
        correct = 0

        for line in lines[1:]:
            if "*" in line:
                correct = len(options)
                options.append(line[3:].replace("*", "").strip())
            elif line.startswith(("A:", "B:", "C:", "D:")):
                options.append(line[3:].strip())

        if len(options) == 4:
            full_question = q_text
            if z_line:
                full_question = f"[{z_line}]\n{q_text}"

            questions.append((full_question, options, correct))

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
    print("POLL:", r.text)


# ================= MAIN =================

state = load_state()

with open(FILE, "r", encoding="utf-8") as f:
    all_q = parse_questions(f.read())

print("TOTAL QUESTIONS:", len(all_q))

for q in all_q:
    q_hash = hash_question(q[0])

    if q_hash in state["used"]:
        continue   # ❌ duplicate skip

    send_poll(q[0], q[1], q[2])
    state["used"].append(q_hash)
    save_state(state)
    break   # 👉 हर run में सिर्फ 1 नया question
