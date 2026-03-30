"""
LINE Chatbot — Student Support Hub
Built for Ethan's dropout prevention initiative
Connects at-risk students to counselors, tutors, scholarships, and job contacts.

Uses line-bot-sdk v2 style API for maximum compatibility.
"""

import os
import json
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
    FlexSendMessage,
)

app = Flask(__name__)

# ─── Configuration ───────────────────────────────────────────────
CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "YOUR_CHANNEL_SECRET")
CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "YOUR_ACCESS_TOKEN")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# ─── Contact Data ────────────────────────────────────────────────
DATA_FILE = os.path.join(os.path.dirname(__file__), "contacts.json")


def load_contacts():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_CONTACTS


def save_contacts(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


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
            "role": "Team Lead - General Support",
            "line_id": "@ethan",
            "subjects": ["Math", "Science", "English"],
        }
    ],
    "scholarship": {
        "contact_name": "Ethan",
        "contact_line": "@ethan",
        "google_form_url": "https://docs.google.com/forms/d/e/YOUR_FORM_ID/viewform",
        "google_doc_url": "https://docs.google.com/document/d/YOUR_DOC_ID/edit",
        "description": "We offer guidance on scholarships for students at risk of dropping out. Fill in the form and we will match you with opportunities.",
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
    "admin_ids": [],
}

if not os.path.exists(DATA_FILE):
    save_contacts(DEFAULT_CONTACTS)


# ─── Flex Message Builders ───────────────────────────────────────

def build_main_menu():
    flex_json = {
        "type": "bubble",
        "hero": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "Student Support Hub",
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
                _menu_button("1 - Admissions & Counselor Help", "#1a73e8"),
                _menu_button("2 - Education & Test Support", "#34a853"),
                _menu_button("3 - Scholarship Information", "#ea4335"),
                _menu_button("4 - Job Search Help", "#fbbc04"),
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
    return FlexSendMessage(alt_text="Student Support Hub - Reply 1-4", contents=flex_json)


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


def build_counselor_response(contacts):
    counselors = contacts.get("counselors", [])
    if not counselors:
        return [TextSendMessage(text="No counselors are currently listed. Please check back later.")]

    bubbles = []
    for c in counselors:
        bubble = {
            "type": "bubble",
            "size": "kilo",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "Counselor", "size": "xs", "color": "#1a73e8", "weight": "bold"},
                    {"type": "text", "text": c["name"], "size": "lg", "weight": "bold", "margin": "sm", "wrap": True},
                    {"type": "text", "text": c["role"], "size": "sm", "color": "#666666", "margin": "sm", "wrap": True},
                    {"type": "separator", "margin": "lg"},
                    {"type": "text", "text": "LINE: " + c["line_id"], "size": "sm", "margin": "lg"},
                    {"type": "text", "text": "Email: " + c.get("email", "N/A"), "size": "sm", "margin": "sm", "wrap": True},
                ],
                "paddingAll": "16px",
            },
        }
        bubbles.append(bubble)

    if len(bubbles) == 1:
        flex_content = bubbles[0]
    else:
        flex_content = {"type": "carousel", "contents": bubbles}

    return [
        TextSendMessage(text="Here are the counselors who can help with admissions and guidance:"),
        FlexSendMessage(alt_text="Counselor contacts", contents=flex_content),
    ]


def build_tutor_response(contacts):
    tutors = contacts.get("tutors", [])
    if not tutors:
        return [TextSendMessage(text="No tutors are currently listed. Please check back later.")]

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
                    {"type": "text", "text": "Education Support", "size": "xs", "color": "#34a853", "weight": "bold"},
                    {"type": "text", "text": t["name"], "size": "lg", "weight": "bold", "margin": "sm"},
                    {"type": "text", "text": t["role"], "size": "sm", "color": "#666666", "margin": "sm", "wrap": True},
                    {"type": "text", "text": "Subjects: " + subjects, "size": "sm", "color": "#333333", "margin": "md", "wrap": True},
                    {"type": "separator", "margin": "lg"},
                    {"type": "text", "text": "LINE: " + t["line_id"], "size": "sm", "margin": "lg"},
                ],
                "paddingAll": "16px",
            },
        }
        bubbles.append(bubble)

    if len(bubbles) == 1:
        flex_content = bubbles[0]
    else:
        flex_content = {"type": "carousel", "contents": bubbles}

    return [
        TextSendMessage(text="Here is our education support team - reach out for tutoring, test prep, or study help:"),
        FlexSendMessage(alt_text="Tutor contacts", contents=flex_content),
    ]


def build_scholarship_response(contacts):
    info = contacts.get("scholarship", {})
    flex_json = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "Scholarship Support", "size": "lg", "weight": "bold", "color": "#ea4335"},
                {"type": "text", "text": info.get("description", "Scholarship information available."), "size": "sm", "color": "#666666", "margin": "lg", "wrap": True},
                {"type": "separator", "margin": "xl"},
                {"type": "text", "text": "Contact: " + info.get("contact_name", "Ethan"), "size": "sm", "margin": "lg"},
                {"type": "text", "text": "LINE: " + info.get("contact_line", "N/A"), "size": "sm", "margin": "sm"},
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
                        "label": "Fill Scholarship Form",
                        "uri": info.get("google_form_url", "https://docs.google.com/forms"),
                    },
                    "style": "primary",
                    "color": "#ea4335",
                },
                {
                    "type": "button",
                    "action": {
                        "type": "uri",
                        "label": "View Scholarship Document",
                        "uri": info.get("google_doc_url", "https://docs.google.com/document"),
                    },
                    "style": "secondary",
                },
            ],
            "paddingAll": "12px",
        },
    }
    return [
        TextSendMessage(text="Great that you are looking into scholarships! Here is how to get started:"),
        FlexSendMessage(alt_text="Scholarship info - tap to open form", contents=flex_json),
    ]


def build_job_response(contacts):
    jobs = contacts.get("job_contacts", [])
    if not jobs:
        return [TextSendMessage(text="No job contacts are currently listed. Please check back later.")]

    bubbles = []
    for j in jobs:
        bubble = {
            "type": "bubble",
            "size": "kilo",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "Job Connection", "size": "xs", "color": "#fbbc04", "weight": "bold"},
                    {"type": "text", "text": j["name"], "size": "lg", "weight": "bold", "margin": "sm"},
                    {"type": "text", "text": j.get("company", "") + " - " + j.get("role", ""), "size": "sm", "color": "#666666", "margin": "sm", "wrap": True},
                    {"type": "text", "text": "Industry: " + j.get("industry", "Various"), "size": "sm", "margin": "md"},
                    {"type": "separator", "margin": "lg"},
                    {"type": "text", "text": "LINE: " + j["line_id"], "size": "sm", "margin": "lg"},
                ],
                "paddingAll": "16px",
            },
        }
        bubbles.append(bubble)

    if len(bubbles) == 1:
        flex_content = bubbles[0]
    else:
        flex_content = {"type": "carousel", "contents": bubbles}

    return [
        TextSendMessage(text="Here are contacts from recent job fairs who are open to connecting:"),
        FlexSendMessage(alt_text="Job contacts", contents=flex_content),
    ]


# ─── Admin Commands ──────────────────────────────────────────────

ADMIN_HELP = """Admin Commands:

/add counselor Name | Role | @line_id | email
/add tutor Name | Role | @line_id | Subject1, Subject2
/add job Name | Company | Role | @line_id | Industry
/remove counselor Name
/remove tutor Name
/remove job Name
/set scholarship form <url>
/set scholarship doc <url>
/add admin <user_id>
/list admins

Example:
/add tutor Pim | Math Tutor | @pim123 | Math, Physics"""


def handle_admin_command(user_id, text):
    contacts = load_contacts()
    admin_ids = contacts.get("admin_ids", [])

    if not admin_ids:
        contacts["admin_ids"] = [user_id]
        save_contacts(contacts)
        admin_ids = [user_id]

    if user_id not in admin_ids:
        return "You don't have admin access. Ask an existing admin to add your user ID: " + user_id

    text_lower = text.lower().strip()

    if text_lower in ["/admin", "/help"]:
        return ADMIN_HELP

    if text_lower == "/list admins":
        admins = contacts.get("admin_ids", [])
        return "Admin IDs:\n" + "\n".join(admins) if admins else "No admins set."

    if text_lower.startswith("/add admin "):
        new_id = text[11:].strip()
        if new_id not in contacts["admin_ids"]:
            contacts["admin_ids"].append(new_id)
            save_contacts(contacts)
        return "Added admin: " + new_id

    if text_lower.startswith("/add counselor "):
        parts = text[15:].split("|")
        if len(parts) < 4:
            return "Format: /add counselor name | role | line_id | email"
        entry = {"name": parts[0].strip(), "role": parts[1].strip(), "line_id": parts[2].strip(), "email": parts[3].strip()}
        contacts["counselors"].append(entry)
        save_contacts(contacts)
        return "Added counselor: " + entry["name"]

    if text_lower.startswith("/add tutor "):
        parts = text[11:].split("|")
        if len(parts) < 4:
            return "Format: /add tutor name | role | line_id | subjects"
        entry = {"name": parts[0].strip(), "role": parts[1].strip(), "line_id": parts[2].strip(), "subjects": [s.strip() for s in parts[3].split(",")]}
        contacts["tutors"].append(entry)
        save_contacts(contacts)
        return "Added tutor: " + entry["name"]

    if text_lower.startswith("/add job "):
        parts = text[9:].split("|")
        if len(parts) < 5:
            return "Format: /add job name | company | role | line_id | industry"
        entry = {"name": parts[0].strip(), "company": parts[1].strip(), "role": parts[2].strip(), "line_id": parts[3].strip(), "industry": parts[4].strip()}
        contacts["job_contacts"].append(entry)
        save_contacts(contacts)
        return "Added job contact: " + entry["name"]

    if text_lower.startswith("/remove counselor "):
        name = text[18:].strip()
        before = len(contacts["counselors"])
        contacts["counselors"] = [c for c in contacts["counselors"] if c["name"].lower() != name.lower()]
        save_contacts(contacts)
        return ("Removed counselor: " + name) if len(contacts["counselors"]) < before else ("Counselor not found: " + name)

    if text_lower.startswith("/remove tutor "):
        name = text[14:].strip()
        before = len(contacts["tutors"])
        contacts["tutors"] = [t for t in contacts["tutors"] if t["name"].lower() != name.lower()]
        save_contacts(contacts)
        return ("Removed tutor: " + name) if len(contacts["tutors"]) < before else ("Tutor not found: " + name)

    if text_lower.startswith("/remove job "):
        name = text[12:].strip()
        before = len(contacts["job_contacts"])
        contacts["job_contacts"] = [j for j in contacts["job_contacts"] if j["name"].lower() != name.lower()]
        save_contacts(contacts)
        return ("Removed job contact: " + name) if len(contacts["job_contacts"]) < before else ("Job contact not found: " + name)

    if text_lower.startswith("/set scholarship form "):
        contacts["scholarship"]["google_form_url"] = text[22:].strip()
        save_contacts(contacts)
        return "Scholarship form URL updated."

    if text_lower.startswith("/set scholarship doc "):
        contacts["scholarship"]["google_doc_url"] = text[21:].strip()
        save_contacts(contacts)
        return "Scholarship doc URL updated."

    return "Unknown command. Type /admin for help."


# ─── Webhook ─────────────────────────────────────────────────────

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()
    contacts = load_contacts()

    # Admin commands
    if text.startswith("/"):
        reply = handle_admin_command(user_id, text)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    # Main menu triggers
    text_lower = text.lower()
    if text_lower in ["hi", "hello", "menu", "start", "help", "hey"]:
        line_bot_api.reply_message(event.reply_token, build_main_menu())
        return

    # Option 1: Counselor
    if text in ["1"] or "counselor" in text_lower or "admission" in text_lower:
        messages = build_counselor_response(contacts)
        line_bot_api.reply_message(event.reply_token, messages)
        return

    # Option 2: Education
    if text in ["2"] or "tutor" in text_lower or "education" in text_lower or "test" in text_lower or "study" in text_lower:
        messages = build_tutor_response(contacts)
        line_bot_api.reply_message(event.reply_token, messages)
        return

    # Option 3: Scholarship
    if text in ["3"] or "scholarship" in text_lower:
        messages = build_scholarship_response(contacts)
        line_bot_api.reply_message(event.reply_token, messages)
        return

    # Option 4: Job
    if text in ["4"] or "job" in text_lower or "work" in text_lower or "career" in text_lower:
        messages = build_job_response(contacts)
        line_bot_api.reply_message(event.reply_token, messages)
        return

    # Default: show menu
    line_bot_api.reply_message(
        event.reply_token,
        [
            TextSendMessage(text="Welcome! Let me help you find the right support."),
            build_main_menu(),
        ],
    )


# ─── Health check ────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def health():
    return "Student Support Hub Bot is running!"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
