import requests, os

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

FILE = "pyq_data/marathi.txt"
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1"))


def parse_blocks(text):
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


def send_poll(block):
    z = ""
    q = ""
    options = []
    correct = 0

    for line in block:
        if line.startswith("Z:"):
            z = line[2:].strip()
        elif line.startswith("Q:"):
            q = line[2:].strip()
        elif line.startswith(("A:", "B:", "C:", "D:")):
            if "*" in line:
                correct = len(options)
                options.append(line[3:].replace("*", "").strip())
            else:
                options.append(line[3:].strip())

    poll_q = f"➤ {q}"
    if z:
        poll_q = f"[{z}]\n\u200b\n{poll_q}"

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPoll"
    payload = {
        "chat_id": CHANNEL_ID,
        "question": poll_q,
        "options": options,
        "type": "quiz",
        "correct_option_id": correct,
        "is_anonymous": True
    }

    r = requests.post(url, json=payload)
    print("POLL:", r.text)


# ================= MAIN =================

with open(FILE, "r", encoding="utf-8") as f:
    text = f.read()

blocks = parse_blocks(text)
print("TOTAL QUESTIONS BEFORE:", len(blocks))

to_post = blocks[:BATCH_SIZE]
remaining = blocks[BATCH_SIZE:]

for block in to_post:
    send_poll(block)

# 🔥 WRITE BACK ONLY REMAINING QUESTIONS
with open(FILE, "w", encoding="utf-8") as f:
    for block in remaining:
        for line in block:
            f.write(line + "\n")
        f.write("\n")

print("POSTED:", len(to_post))
print("REMAINING:", len(remaining))
