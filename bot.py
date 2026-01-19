import requests, os, random

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

FILE = "pyq_data/marathi.txt"
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1"))  # eg. 10 morning / 10 evening


def parse_questions(text):
    lines = [l.rstrip() for l in text.splitlines() if l.strip()]
    questions = []

    i = 0
    while i < len(lines):
        z_line = ""
        if lines[i].startswith("Z:"):
            z_line = lines[i][2:].strip()
            i += 1

        if i >= len(lines) or not lines[i].startswith("Q:"):
            i += 1
            continue

        raw_q = lines[i][2:].strip()
        i += 1

        options = []
        correct = 0

        for _ in range(4):
            if i >= len(lines):
                break
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


# ================= MAIN =================

with open(FILE, "r", encoding="utf-8") as f:
    questions = parse_questions(f.read())

print("TOTAL QUESTIONS AVAILABLE:", len(questions))

if not questions:
    print("❌ No questions found")
    exit()

# 🔀 RANDOM selection (duplicates allowed)
selected = random.sample(questions, k=min(BATCH_SIZE, len(questions)))

for q in selected:
    send_poll(q["poll"], q["options"], q["correct"])