import requests, os, json, hashlib, subprocess

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


# ---- NEW (tiny helper, बाकी logic untouched) ----
def split_blocks(text):
    blocks = []
    current = []
    for line in text.splitlines():
        if line.strip() == "" and current:
            blocks.append(current)
            current = []
        else:
            if line.strip():
                current.append(line.rstrip())
    if current:
        blocks.append(current)
    return blocks


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
                poll_q = f"[{z_line}]\n\u200b\n➤ {raw_q}"
            else:
                poll_q = f"➤ {raw_q}"

            questions.append({
                "raw": raw_q,
                "poll": poll_q,
                "options": options,
                "correct": correct
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
    return r.status_code == 200


# ================= MAIN =================

state = load_state()

with open(FILE, "r", encoding="utf-8") as f:
    original_text = f.read()

questions = parse_questions(original_text)
blocks = split_blocks(original_text)

print("TOTAL QUESTIONS:", len(questions))

posted = 0

for q in questions:
    h = hash_q(q["raw"])
    if h in state["used"]:
        continue

    ok = send_poll(q["poll"], q["options"], q["correct"])
    if not ok:
        break

    state["used"].append(h)
    posted += 1

    if posted >= BATCH_SIZE:
        break

# ---- 🔥 ONLY THIS FEATURE: remove posted questions ----
if posted > 0:
    remaining_blocks = blocks[posted:]

    with open(FILE, "w", encoding="utf-8") as f:
        for b in remaining_blocks:
            for line in b:
                f.write(line + "\n")
            f.write("\n")

    # commit back to GitHub
    subprocess.run(["git", "config", "user.name", "github-actions"])
    subprocess.run(["git", "config", "user.email", "github-actions@github.com"])
    subprocess.run(["git", "add", FILE])
    subprocess.run(["git", "commit", "-m", f"Remove {posted} posted questions"])
    subprocess.run(["git", "push"])

save_state(state)
