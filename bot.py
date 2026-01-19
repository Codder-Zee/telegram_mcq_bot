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
        state = json.load(f)
    if "used" not in state:
        state["used"] = []
    return state


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def hash_q(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()


# ================= PARSER =================

def parse_questions(original_text):
    original_lines = original_text.splitlines()
    clean_lines = [l.rstrip() for l in original_lines if l.strip()]

    questions = []
    i = 0
    while i < len(clean_lines):
        z_line = ""
        if clean_lines[i].startswith("Z:"):
            z_line = clean_lines[i]
            i += 1

        if i >= len(clean_lines) or not clean_lines[i].startswith("Q:"):
            i += 1
            continue

        raw_q = clean_lines[i][2:].strip()
        i += 1

        options = []
        correct = 0

        for _ in range(4):
            line = clean_lines[i]
            if "*" in line:
                correct = len(options)
                options.append(line[3:].replace("*", "").strip())
            else:
                options.append(line[3:].strip())
            i += 1

        poll_q = f"➤ {raw_q}"
        if z_line:
            poll_q = f"[{z_line[2:].strip()}]\n\u200b\n{poll_q}"

        # 🔥 original block text (for safe deletion)
        block = []
        if z_line:
            block.append(z_line)
        block.append("Q: " + raw_q)
        for idx, opt in enumerate(options):
            prefix = chr(65 + idx) + ": "
            if idx == correct:
                block.append(prefix + opt + " *")
            else:
                block.append(prefix + opt)

        questions.append({
            "raw": raw_q,
            "poll": poll_q,
            "options": options,
            "correct": correct,
            "block": "\n".join(block)
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
    original_text = f.read()

questions = parse_questions(original_text)
print("TOTAL QUESTIONS:", len(questions))

posted_blocks = []
posted = 0

for q in questions:
    h = hash_q(q["raw"])
    if h in state["used"]:
        continue

    send_poll(q["poll"], q["options"], q["correct"])
    state["used"].append(h)
    posted_blocks.append(q["block"])
    posted += 1

    if posted >= BATCH_SIZE:
        break

# 🔥 REMOVE POSTED QUESTIONS FROM FILE
if posted_blocks:
    updated_text = original_text
    for block in posted_blocks:
        updated_text = updated_text.replace(block, "").strip()

    with open(FILE, "w", encoding="utf-8") as f:
        f.write(updated_text + "\n")

save_state(state)
