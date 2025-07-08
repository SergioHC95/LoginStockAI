import os
import json
import imaplib
import poplib
import email
from email.parser import BytesParser
from email.header import decode_header
from email.utils import parsedate_to_datetime
from tqdm import tqdm
from datetime import datetime, timedelta, timezone
from pathlib import Path
from .utils import parse_email, clean_filename

def load_config():
    config_path = Path(__file__).parent / "config.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def fetch_emails(email_dir="emails", state_file="last_fetch.json"):
    config = load_config()
    os.makedirs(email_dir, exist_ok=True)

    def save_last_fetch_time(dt):
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump({"last_fetch": dt.isoformat()}, f)

    def load_last_fetch_time():
        if os.path.exists(state_file):
            with open(state_file, "r", encoding="utf-8") as f:
                return datetime.fromisoformat(json.load(f)["last_fetch"])
        return None

    source = config.get("source", "imap")  # default to imap
    last_fetch = load_last_fetch_time()
    one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)
    fetch_start_time = datetime.now(timezone.utc)
    since_dt = max(last_fetch or one_year_ago, one_year_ago)
    seen_one = False
    count = 0

    if source == "imap":
        print(f"📡 Connecting to IMAP: {config['server']} as {config['email']}")
        mail = imaplib.IMAP4_SSL(config["server"])
        mail.login(config["email"], config["password"])
        mail.select(config.get("mailbox", "INBOX"))

        since_str = since_dt.strftime("%d-%b-%Y")
        result, data = mail.search(None, f'SINCE {since_str}')
        if result != "OK" or not data or not data[0]:
            print("No messages found.")
            mail.logout()
            return

        email_ids = data[0].split()[::-1]
        print(f"📬 Found {len(email_ids)} IMAP emails since {since_str}.")

        for eid in tqdm(email_ids, desc="Fetching new IMAP emails"):
            result, msg_data = mail.fetch(eid, "(RFC822)")
            if result != "OK":
                continue

            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)
            parsed = parse_email(msg, raw)

            try:
                msg_dt = parsedate_to_datetime(parsed["date"]).astimezone(timezone.utc)
            except Exception:
                continue

            if msg_dt < one_year_ago:
                break
            if last_fetch and msg_dt <= last_fetch:
                break

            if not seen_one:
                save_last_fetch_time(fetch_start_time)
                seen_one = True

            fname = clean_filename(parsed, count)
            with open(os.path.join(email_dir, fname), "w", encoding="utf-8") as f:
                json.dump(parsed, f, indent=2, ensure_ascii=False)
            count += 1

        mail.logout()

    elif source == "pop":
        print(f"📡 Connecting to POP3: {config['server']} as {config['email']}")
        try:
            pop = poplib.POP3_SSL(config["server"], config.get("port", 995))
            pop.user(config["email"])
            pop.pass_(config["password"])
        except poplib.error_proto as e:
            print(f"❌ POP3 authentication failed: {e}")
            return

        num_messages = len(pop.list()[1])
        print(f"📬 Found {num_messages} POP3 emails (scanning newest to oldest)")

        for i in tqdm(range(num_messages, 0, -1), desc="Fetching new POP3 emails"):
            raw_lines = pop.retr(i)[1]
            raw = b"\n".join(raw_lines)
            msg = BytesParser().parsebytes(raw)
            parsed = parse_email(msg, raw)

            try:
                msg_dt = parsedate_to_datetime(parsed["date"]).astimezone(timezone.utc)
            except Exception:
                continue

            if msg_dt < one_year_ago:
                break
            if last_fetch and msg_dt <= last_fetch:
                break

            if not seen_one:
                save_last_fetch_time(fetch_start_time)
                seen_one = True

            fname = clean_filename(parsed, count)
            with open(os.path.join(email_dir, fname), "w", encoding="utf-8") as f:
                json.dump(parsed, f, indent=2, ensure_ascii=False)
            count += 1

        pop.quit()

    else:
        raise ValueError(f"❗ Unknown source '{source}' in config.")

if __name__ == "__main__":
    fetch_emails()
