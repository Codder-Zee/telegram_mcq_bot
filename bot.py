import requests, os, json, time

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

print("BOT_TOKEN:", "OK" if BOT_TOKEN else "MISSING")
print("CHANNEL_ID:", CHANNEL_ID)

FILES = {
    "marathi": "pyq_data/marathi.txt",
    "hindi": "pyq_data/hindi.txt",
    "english": "pyq_data/english.txt"
}

STATE_FILE = "state.json"


def parse_questions(text):
    blocks = text.strip().split("\n\n")
    questions = []

    for b in blocks:
        lines = b.split("\n")
        if len(lines) < 5:
            continue

        q = lines[0].replace("Q:", "").strip()
        options = []
        correct = 0

        for line in lines[1:]:
            if "*" in line:
                correct = len(options)
                options.append(line[3:].replace("*", "").strip())
            elif line.startswith(("A:", "B:", "C:", "D:")):
                options.append(line[3:].strip())

        if len(options) == 4:
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
    print("POLL RESPONSE:", r.text)
    return r.json()


# ===== MAIN =====

all_q = []

for f in FILES.values():
    with open(f, "r", encoding="utf-8") as file:
        all_q.extend(parse_questions(file.read()))

print("TOTAL QUESTIONS FOUND:", len(all_q))

if not all_q:
    print("❌ NO QUESTIONS PARSED — FORMAT ISSUE")
    exit()

q = all_q[0]
send_poll(q[0], q[1], q[2])
