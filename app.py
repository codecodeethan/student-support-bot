"""
LINE Chatbot — Student Support Hub
Built for Ethan's dropout prevention initiative
Connects at-risk students to counselors, tutors, scholarships, and job contacts.
"""

import os
import json
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    FlexMessage,
    FlexContainer,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.exceptions import InvalidSignatureError

app = Flask(__name__)

# ─── Configuration ───────────────────────────────────────────────
# Set these as environment variables on your hosting platform
CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "YOUR_CHANNEL_SECRET")
CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "YOUR_ACCESS_TOKEN")

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# ─── Editable Contact Data (loaded from JSON file) ──────────────
DATA_FILE = os.path.join(os.path.dirname(__file__), "contacts.json")


def load_contacts():
    """Load contacts from JSON file."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_CONTACTS


def save_contacts(data):
    """Save contacts to JSON file."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# Default contacts — edit contacts.json or use admin commands in chat
DEFAULT_CONTACTS = {
    "counselors": [
        {
            "name": "Khun Somporn (Thai Counselor)",
            "role": "Admissions & Academic Guidance",
            "line_id": "@counselor1",
            "email": "somporn@school.ac.th",
        }
    ],
    "tutors": [
        {
            "name": "Ethan",
            "role": "Team Lead — General Support",
            "line_id": "@ethan",
            "subjects": ["Math", "Science", "English"],
        }
    ],
    "scholarship": {
        "contact_name": "Ethan",
        "contact_line": "@ethan",
        "google_form_url": "https://docs.google.com/forms/d/e/YOUR_FORM_ID/viewform",
        "google_doc_url": "https://docs.google.com/document/d/YOUR_DOC_ID/edit",
        "description": "We offer guidance on scholarships for students at risk of dropping out. Fill in the form below and we'll match you with opportunities.",
    },
    "job_contacts": [
        {
            "name": "Contact from Job Fair",
            "company": "Company Name",
            "role": "HR / Recruiter",
            "line_id": "@jobcontact1",
            "industry": "Technology",
        }
    ],
    "admin_ids": [],  # Add LINE user IDs of people allowed to edit contacts
}

# Initialize contacts file if it doesn't exist
if not os.path.exists(DATA_FILE):
    save_contacts(DEFAULT_CONTACTS)


# ─── Flex Message Builders ───────────────────────────────────────

def build_main_menu():
    """Build the main menu as a Flex Message."""
    flex_json = {
        "type": "bubble",
        "hero": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "🎓 Student Support Hub",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#1a73e8",
                    "align": "center",
                },
                {
                    "type": "text",
                    "text": "How can we help you today?",
                    "size": "sm",
                    "color": "#666666",
                    "align": "center",
                    "margin": "md",
                },
            ],
            "paddingAll": "20px",
            "backgroundColor": "#f0f6ff",
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": [
                _menu_button("1️⃣  Admissions & Counselor Help", "#1a73e8"),
                _menu_button("2️⃣  Education & Test Support", "#34a853"),
                _menu_button("3️⃣  Scholarship Information", "#ea4335"),
                _menu_button("4️⃣  Job Search Help", "#fbbc04"),
            ],
            "paddingAll": "16px",
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "Reply with a number (1-4) to get started",
                    "size": "xs",
                    "color": "#999999",
                    "align": "center",
                }
            ],
            "paddingAll": "12px",
        },
    }
    return FlexMessage(
        alt_text="Student Support Hub — Reply 1-4 to get started",
        contents=FlexContainer.from_dict(flex_json),
    )


def _menu_button(label, color):
    return {
        "type": "box",
        "layout": "horizontal",
        "contents": [
            {
                "type": "text",
                "text": label,
                "size": "md",
                "color": "#333333",
                "flex": 1,
                "gravity": "center",
            }
        ],
        "paddingAll": "14px",
        "backgroundColor": "#ffffff",
        "cornerRadius": "8px",
        "borderWidth": "1px",
        "borderColor": color,
    }


def build_counselor_card(contacts):
    """Build counselor contact cards."""
    counselors = contacts.get("counselors", [])
    if not counselors:
        return TextMessage(text="No counselors are currently listed. Please check back later.")

    bubbles = []
    for c in counselors:
        bubble = {
            "type": "bubble",
            "size": "kilo",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "🏫 Counselor",
                        "size": "xs",
                        "color": "#1a73e8",
                        "weight": "bold",
                    },
                    {
                        "type": "text",
                        "text": c["name"],
                        "size": "lg",
                        "weight": "bold",
                        "margin": "sm",
                        "wrap": True,
                    },
                    {
                        "type": "text",
                        "text": c["role"],
                        "size": "sm",
                        "color": "#666666",
                        "margin": "sm",
                        "wrap": True,
                    },
                    {"type": "separator", "margin": "lg"},
                    {
                        "type": "text",
                        "text": f"LINE: {c['line_id']}",
                        "size": "sm",
                        "margin": "lg",
                    },
                    {
                        "type": "text",
                        "text": f"Email: {c.get('email', 'N/A')}",
                        "size": "sm",
                        "margin": "sm",
                        "wrap": True,
                    },
                ],
                "paddingAll": "16px",
            },
        }
        bubbles.append(bubble)

    if len(bubbles) == 1:
        flex_json = bubbles[0]
    else:
        flex_json = {"type": "carousel", "contents": bubbles}

    return FlexMessage(
        alt_text="Here are the counselors you can contact",
        contents=FlexContainer.from_dict(flex_json),
    )


def build_tutor_card(contacts):
    """Build tutor/education support cards."""
    tutors = contacts.get("tutors", [])
    if not tutors:
        return TextMessage(text="No tutors are currently listed. Please check back later.")

    bubbles = []
    for t in tutors:
        subjects = ", ".join(t.get("subjects", ["General"]))
        bubble = {
            "type": "bubble",
            "size": "kilo",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "📚 Education Support",
                        "size": "xs",
                        "color": "#34a853",
                        "weight": "bold",
                    },
                    {
                        "type": "text",
                        "text": t["name"],
                        "size": "lg",
                        "weight": "bold",
                        "margin": "sm",
                    },
                    {
                        "type": "text",
                        "text": t["role"],
                        "size": "sm",
                        "color": "#666666",
                        "margin": "sm",
                        "wrap": True,
                    },
                    {
                        "type": "text",
                        "text": f"Subjects: {subjects}",
                        "size": "sm",
                        "color": "#333333",
                        "margin": "md",
                        "wrap": True,
                    },
                    {"type": "separator", "margin": "lg"},
                    {
                        "type": "text",
                        "text": f"LINE: {t['line_id']}",
                        "size": "sm",
                        "margin": "lg",
                    },
                ],
                "paddingAll": "16px",
            },
        }
        bubbles.append(bubble)

    if len(bubbles) == 1:
        flex_json = bubbles[0]
    else:
        flex_json = {"type": "carousel", "contents": bubbles}

    return FlexMessage(
        alt_text="Here are tutors who can help you",
        contents=FlexContainer.from_dict(flex_json),
    )


def build_scholarship_card(contacts):
    """Build scholarship info with Google Doc links."""
    info = contacts.get("scholarship", {})
    flex_json = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "🎓 Scholarship Support",
                    "size": "lg",
                    "weight": "bold",
                    "color": "#ea4335",
                },
                {
                    "type": "text",
                    "text": info.get("description", "Scholarship information available."),
                    "size": "sm",
                    "color": "#666666",
                    "margin": "lg",
                    "wrap": True,
                },
                {"type": "separator", "margin": "xl"},
                {
                    "type": "text",
                    "text": f"Contact: {info.get('contact_name', 'Ethan')}",
                    "size": "sm",
                    "margin": "lg",
                },
                {
                    "type": "text",
                    "text": f"LINE: {info.get('contact_line', 'N/A')}",
                    "size": "sm",
                    "margin": "sm",
                },
            ],
            "paddingAll": "20px",
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "uri",
                        "label": "📝 Fill Scholarship Form",
                        "uri": info.get(
                            "google_form_url",
                            "https://docs.google.com/forms",
                        ),
                    },
                    "style": "primary",
                    "color": "#ea4335",
                },
                {
                    "type": "button",
                    "action": {
                        "type": "uri",
                        "label": "📄 View Scholarship Document",
                        "uri": info.get(
                            "google_doc_url",
                            "https://docs.google.com/document",
                        ),
                    },
                    "style": "secondary",
                },
            ],
            "paddingAll": "12px",
        },
    }
    return FlexMessage(
        alt_text="Scholarship info — tap to open the form",
        contents=FlexContainer.from_dict(flex_json),
    )


def build_job_card(contacts):
    """Build job contact cards."""
    jobs = contacts.get("job_contacts", [])
    if not jobs:
        return TextMessage(text="No job contacts are currently listed. Please check back later.")

    bubbles = []
    for j in jobs:
        bubble = {
            "type": "bubble",
            "size": "kilo",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "💼 Job Connection",
                        "size": "xs",
                        "color": "#fbbc04",
                        "weight": "bold",
                    },
                    {
                        "type": "text",
                        "text": j["name"],
                        "size": "lg",
                        "weight": "bold",
                        "margin": "sm",
                    },
                    {
                        "type": "text",
                        "text": f"{j.get('company', '')} — {j.get('role', '')}",
                        "size": "sm",
                        "color": "#666666",
                        "margin": "sm",
                        "wrap": True,
                    },
                    {
                        "type": "text",
                        "text": f"Industry: {j.get('industry', 'Various')}",
                        "size": "sm",
                        "margin": "md",
                    },
                    {"type": "separator", "margin": "lg"},
                    {
                        "type": "text",
                        "text": f"LINE: {j['line_id']}",
                        "size": "sm",
                        "margin": "lg",
                    },
                ],
                "paddingAll": "16px",
            },
        }
        bubbles.append(bubble)

    if len(bubbles) == 1:
        flex_json = bubbles[0]
    else:
        flex_json = {"type": "carousel", "contents": bubbles}

    return FlexMessage(
        alt_text="Here are job contacts from recent job fairs",
        contents=FlexContainer.from_dict(flex_json),
    )


# ─── Admin Commands ──────────────────────────────────────────────

ADMIN_HELP = """🔧 Admin Commands:

/add counselor <name> | <role> | <line_id> | <email>
/add tutor <name> | <role> | <line_id> | <subjects comma-separated>
/add job <name> | <company> | <role> | <line_id> | <industry>
/remove counselor <name>
/remove tutor <name>
/remove job <name>
/set scholarship form <url>
/set scholarship doc <url>
/list admins
/add admin <user_id>

Example:
/add tutor Pim | Math Tutor | @pim123 | Math, Physics"""


def handle_admin_command(user_id, text):
    """Process admin commands to edit contacts."""
    contacts = load_contacts()
    admin_ids = contacts.get("admin_ids", [])

    # Allow first user to become admin if none exist
    if not admin_ids:
        contacts["admin_ids"] = [user_id]
        save_contacts(contacts)
        admin_ids = [user_id]
        # Fall through to process the command

    if user_id not in admin_ids:
        return "⛔ You don't have admin access. Ask an existing admin to add your user ID."

    text_lower = text.lower().strip()

    if text_lower == "/admin" or text_lower == "/help":
        return ADMIN_HELP

    if text_lower == "/list admins":
        admins = contacts.get("admin_ids", [])
        return "👤 Admin IDs:\n" + "\n".join(admins) if admins else "No admins set."

    if text_lower.startswith("/add admin "):
        new_id = text[11:].strip()
        if new_id not in contacts["admin_ids"]:
            contacts["admin_ids"].append(new_id)
            save_contacts(contacts)
        return f"✅ Added admin: {new_id}"

    if text_lower.startswith("/add counselor "):
        parts = text[15:].split("|")
        if len(parts) < 4:
            return "❌ Format: /add counselor name | role | line_id | email"
        entry = {
            "name": parts[0].strip(),
            "role": parts[1].strip(),
            "line_id": parts[2].strip(),
            "email": parts[3].strip(),
        }
        contacts["counselors"].append(entry)
        save_contacts(contacts)
        return f"✅ Added counselor: {entry['name']}"

    if text_lower.startswith("/add tutor "):
        parts = text[11:].split("|")
        if len(parts) < 4:
            return "❌ Format: /add tutor name | role | line_id | subjects"
        entry = {
            "name": parts[0].strip(),
            "role": parts[1].strip(),
            "line_id": parts[2].strip(),
            "subjects": [s.strip() for s in parts[3].split(",")],
        }
        contacts["tutors"].append(entry)
        save_contacts(contacts)
        return f"✅ Added tutor: {entry['name']}"

    if text_lower.startswith("/add job "):
        parts = text[9:].split("|")
        if len(parts) < 5:
            return "❌ Format: /add job name | company | role | line_id | industry"
        entry = {
            "name": parts[0].strip(),
            "company": parts[1].strip(),
            "role": parts[2].strip(),
            "line_id": parts[3].strip(),
            "industry": parts[4].strip(),
        }
        contacts["job_contacts"].append(entry)
        save_contacts(contacts)
        return f"✅ Added job contact: {entry['name']}"

    if text_lower.startswith("/remove counselor "):
        name = text[18:].strip()
        before = len(contacts["counselors"])
        contacts["counselors"] = [c for c in contacts["counselors"] if c["name"].lower() != name.lower()]
        save_contacts(contacts)
        if len(contacts["counselors"]) < before:
            return f"✅ Removed counselor: {name}"
        return f"❌ Counselor '{name}' not found."

    if text_lower.startswith("/remove tutor "):
        name = text[14:].strip()
        before = len(contacts["tutors"])
        contacts["tutors"] = [t for t in contacts["tutors"] if t["name"].lower() != name.lower()]
        save_contacts(contacts)
        if len(contacts["tutors"]) < before:
            return f"✅ Removed tutor: {name}"
        return f"❌ Tutor '{name}' not found."

    if text_lower.startswith("/remove job "):
        name = text[12:].strip()
        before = len(contacts["job_contacts"])
        contacts["job_contacts"] = [j for j in contacts["job_contacts"] if j["name"].lower() != name.lower()]
        save_contacts(contacts)
        if len(contacts["job_contacts"]) < before:
            return f"✅ Removed job contact: {name}"
        return f"❌ Job contact '{name}' not found."

    if text_lower.startswith("/set scholarship form "):
        url = text[22:].strip()
        contacts["scholarship"]["google_form_url"] = url
        save_contacts(contacts)
        return f"✅ Scholarship form URL updated."

    if text_lower.startswith("/set scholarship doc "):
        url = text[21:].strip()
        contacts["scholarship"]["google_doc_url"] = url
        save_contacts(contacts)
        return f"✅ Scholarship doc URL updated."

    return "❓ Unknown command. Type /admin for help."


# ─── Message Handler ─────────────────────────────────────────────

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()
    contacts = load_contacts()

    with ApiClient(configuration) as api_client:
        api = MessagingApi(api_client)

        # ── Admin commands ──
        if text.startswith("/"):
            reply_text = handle_admin_command(user_id, text)
            api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)],
                )
            )
            return

        # ── Main menu triggers ──
        text_lower = text.lower()
        if text_lower in ["hi", "hello", "menu", "start", "help", "สวัสดี", "เมนู"]:
            api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[build_main_menu()],
                )
            )
            return

        # ── Option routing ──
        if text in ["1", "1️⃣"] or "counselor" in text_lower or "admission" in text_lower or "ที่ปรึกษา" in text_lower:
            api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(text="Here are the counselors who can help with admissions and guidance:"),
                        build_counselor_card(contacts),
                    ],
                )
            )
            return

        if text in ["2", "2️⃣"] or "tutor" in text_lower or "education" in text_lower or "test" in text_lower or "study" in text_lower or "สอน" in text_lower:
            api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(text="Here's our education support team — reach out for tutoring, test prep, or study help:"),
                        build_tutor_card(contacts),
                    ],
                )
            )
            return

        if text in ["3", "3️⃣"] or "scholarship" in text_lower or "ทุน" in text_lower:
            api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(text="Great that you're looking into scholarships! Here's how to get started:"),
                        build_scholarship_card(contacts),
                    ],
                )
            )
            return

        if text in ["4", "4️⃣"] or "job" in text_lower or "work" in text_lower or "career" in text_lower or "งาน" in text_lower:
            api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(text="Here are contacts from recent job fairs who are open to connecting:"),
                        build_job_card(contacts),
                    ],
                )
            )
            return

        # ── Default: show menu ──
        api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    TextMessage(text="Welcome! 👋 Let me help you find the right support."),
                    build_main_menu(),
                ],
            )
        )


# ─── Health check for Railway/Render ─────────────────────────────

@app.route("/", methods=["GET"])
def health():
    return "Student Support Hub Bot is running! 🎓"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
