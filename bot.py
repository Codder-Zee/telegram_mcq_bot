import requests, os, json, hashlib

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

FILE = "pyq_data/marathi.txt"
STATE_FILE = "state.json"
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1"))


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


def hash_q(raw_q):
    return hashlib.md5(raw_q.encode("utf-8")).hexdigest()


def parse_questions(text):
    lines = [l.rstrip() for l in text.splitlines() if l.strip()]
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

        raw_q = lines[i][2:].strip()
        block_start = i - (1 if z_line else 0)
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

        block_end = i

        if len(options) == 4:
            if z_line:
                poll_q = f"[{z_line}]\n\u200b\n➤ {raw_q}"
            else:
                poll_q = f"➤ {raw_q}"

            questions.append({
                "raw": raw_q,
                "poll": poll_q,
                "options": options,
                "correct": correct,
                "start": block_start,
                "end": block_end
            })

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
    original_text = f.read()

questions = parse_questions(original_text)

print("TOTAL QUESTIONS:", len(questions))

posted = 0
remove_blocks = []

for q in questions:
    h = hash_q(q["raw"])

    if h in state["used"]:
        continue

    send_poll(q["poll"], q["options"], q["correct"])
    state["used"].append(h)
    posted += 1

    remove_blocks.append((q["start"], q["end"]))

    if posted >= BATCH_SIZE:
        break


# 🔥 REMOVE POSTED QUESTIONS FROM FILE
if remove_blocks:
    lines = original_text.splitlines()
    new_lines = []

    for idx, line in enumerate(lines):
        keep = True
        for s, e in remove_blocks:
            if s <= idx < e:
                keep = False
                break
        if keep:
            new_lines.append(line)

    with open(FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines).strip() + "\n")

save_state(state)
