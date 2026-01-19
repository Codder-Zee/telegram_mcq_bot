import requests, os, json, hashlib

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

FILE = "pyq_data/marathi.txt"
STATE_FILE = "state.json"
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1"))


# ================= STATE =================

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


# ================= PARSER =================

def parse_questions(text):
    lines = [l.rstrip() for l in text.splitlines() if l.strip()]
    questions = []

    i = 0
    while i < len(lines):
        z = None
        if lines[i].startswith("Z:"):
            z = lines[i]
            i += 1

        if i >= len(lines) or not lines[i].startswith("Q:"):
            i += 1
            continue

        q_line = lines[i]
        raw_q = q_line[2:].strip()
        i += 1

        opts = []
        correct = 0

        for _ in range(4):
            line = lines[i]
            if "*" in line:
                correct = len(opts)
                opts.append(line[3:].replace("*", "").strip())
            else:
                opts.append(line[3:].strip())
            i += 1

        poll_q = f"➤ {raw_q}"
        if z:
            poll_q = f"[{z[2:].strip()}]\n\u200b\n{poll_q}"

        questions.append({
            "hash": hash_q(raw_q),
            "poll": poll_q,
            "options": opts,
            "correct": correct,
            "raw_lines": ([z] if z else []) + [q_line] + [
                f"{chr(65+i)}: {opts[i]}" + (" *" if i == correct else "")
                for i in range(4)
            ]
        })

    return questions


# ================= TELEGRAM =================

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
    text = f.read()

questions = parse_questions(text)
print("TOTAL QUESTIONS BEFORE:", len(questions))

remaining_questions = []
posted = 0

for q in questions:
    if q["hash"] in state["used"]:
        continue

    if posted < BATCH_SIZE:
        send_poll(q["poll"], q["options"], q["correct"])
        state["used"].append(q["hash"])
        posted += 1
    else:
        remaining_questions.append(q)

# 🔥 REWRITE FILE WITH ONLY REMAINING QUESTIONS
with open(FILE, "w", encoding="utf-8") as f:
    for q in remaining_questions:
        for line in q["raw_lines"]:
            f.write(line + "\n")
        f.write("\n")

save_state(state)

print("POSTED:", posted)
print("REMAINING:", len(remaining_questions))
