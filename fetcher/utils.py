import base64
from email.header import decode_header
from email.utils import parseaddr, parsedate_to_datetime
from slugify import slugify
from datetime import timezone


def decode_mime_words(s):
    fragments = decode_header(s or "")
    return ''.join(
        frag.decode(enc or "utf-8") if isinstance(frag, bytes) else frag
        for frag, enc in fragments
    )


def parse_email(msg, raw_bytes):
    """Parse an email.message.Message object into a dict with metadata and plain text body."""
    from_email = decode_mime_words(msg.get("From", ""))
    message_id = msg.get("Message-ID", "").strip()
    in_reply_to = msg.get("In-Reply-To", "").strip()
    references = msg.get("References", "").strip()
    subject = decode_mime_words(msg.get("Subject", ""))
    date = msg.get("Date", "")
    body = ""

    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get("Content-Disposition", "")).lower()
            if ctype == "text/plain" and "attachment" not in disp:
                try:
                    body = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="replace")
                    break
                except Exception:
                    continue
    else:
        try:
            body = msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8", errors="replace")
        except Exception:
            body = ""

    return {
        "subject": subject,
        "from": from_email,
        "from_email": parseaddr(from_email)[1],
        "date": date,
        "message_id": message_id,
        "in_reply_to": in_reply_to,
        "references": references.split() if references else [],
        "body": body.strip(),
        "raw_mime_b64": base64.b64encode(raw_bytes).decode("ascii")
    }


def clean_filename(parsed, count):
    try:
        dt = parsedate_to_datetime(parsed["date"]).astimezone(timezone.utc)
        timestamp = dt.strftime("%Y%m%d_%H%M%S")
    except Exception:
        timestamp = f"unknown_{count:05d}"

    sender = parsed.get("from_email", "unknown").replace("@", "_at_").replace(".", "_")
    subject = slugify(parsed.get("subject", "no_subject"))[:40]
    return f"{timestamp}__{sender}__{subject}.json"
