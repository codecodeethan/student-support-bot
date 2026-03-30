"""
LINE Chatbot — Student Support Hub v3
Relay system: students talk to counselors/tutors/job contacts THROUGH the bot.
The bot forwards messages back and forth like a bridge.
"""

import os
import json
import time
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

# ─── Data Files ──────────────────────────────────────────────────
DATA_DIR = os.path.dirname(__file__)
CONTACTS_FILE = os.path.join(DATA_DIR, "contacts.json")
SESSIONS_FILE = os.path.join(DATA_DIR, "sessions.json")

# ─── Sessions: tracks who is talking to whom ─────────────────────
# Structure:
# {
#   "student_user_id": {
#     "connected_to": "counselor_user_id",
#     "connected_name": "Khun Somporn",
#     "category": "counselor",
#     "started": timestamp
#   },
#   "counselor_user_id": {
#     "connected_to": "student_user_id",
#     "connected_name": "Student",
#     "category": "responding",
#     "started": timestamp
#   }
# }


def load_sessions():
    if os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_sessions(sessions):
    with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, indent=2, ensure_ascii=False)


def load_contacts():
    if os.path.exists(CONTACTS_FILE):
        with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    save_contacts(DEFAULT_CONTACTS)
    return DEFAULT_CONTACTS


def save_contacts(data):
    with open(CONTACTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


DEFAULT_CONTACTS = {
    "counselors": [
        {
            "name": "Khun Somporn",
            "role": "Admissions & Academic Guidance",
            "user_id": "",
            "email": "somporn@school.ac.th",
        }
    ],
    "tutors": [
        {
            "name": "Ethan",
            "role": "Team Lead - General Support",
            "user_id": "",
            "subjects": ["Math", "Science", "English"],
        }
    ],
    "scholarship": {
        "contact_name": "Ethan",
        "contact_user_id": "",
        "google_form_url": "https://docs.google.com/forms/d/e/YOUR_FORM_ID/viewform",
        "google_doc_url": "https://docs.google.com/document/d/YOUR_DOC_ID/edit",
        "description": "We offer guidance on scholarships for students at risk of dropping out. Fill in the form and we will match you with opportunities.",
    },
    "job_contacts": [
        {
            "name": "Job Fair Contact",
            "company": "Company Name",
            "role": "HR / Recruiter",
            "user_id": "",
            "industry": "Technology",
        }
    ],
    "admin_ids": [],
}

if not os.path.exists(CONTACTS_FILE):
    save_contacts(DEFAULT_CONTACTS)


# ─── Helper: get user display name ──────────────────────────────

def get_display_name(user_id):
    try:
        profile = line_bot_api.get_profile(user_id)
        return profile.display_name
    except Exception:
        return "Someone"


# ─── Flex Message Builders ───────────────────────────────────────

def build_main_menu():
    flex_json = {
        "type": "bubble",
        "hero": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "Student Support Hub", "weight": "bold", "size": "xl", "color": "#1a73e8", "align": "center"},
                {"type": "text", "text": "How can we help you today?", "size": "sm", "color": "#666666", "align": "center", "margin": "md"},
            ],
            "paddingAll": "20px",
            "backgroundColor": "#f0f6ff",
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": [
                _menu_button("1 - Talk to a Counselor", "#1a73e8"),
                _menu_button("2 - Get Education & Test Help", "#34a853"),
                _menu_button("3 - Scholarship Information", "#ea4335"),
                _menu_button("4 - Job Search Help", "#fbbc04"),
            ],
            "paddingAll": "16px",
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "Reply 1-4 to connect with someone who can help", "size": "xs", "color": "#999999", "align": "center", "wrap": True},
            ],
            "paddingAll": "12px",
        },
    }
    return FlexSendMessage(alt_text="Student Support Hub - Reply 1-4", contents=flex_json)


def _menu_button(label, color):
    return {
        "type": "box",
        "layout": "horizontal",
        "contents": [{"type": "text", "text": label, "size": "md", "color": "#333333", "flex": 1, "gravity": "center"}],
        "paddingAll": "14px",
        "backgroundColor": "#ffffff",
        "cornerRadius": "8px",
        "borderWidth": "1px",
        "borderColor": color,
    }


def build_person_picker(category, contacts):
    """Build a list of available people the student can connect with."""
    if category == "counselor":
        people = contacts.get("counselors", [])
        color = "#1a73e8"
        label = "Counselor"
    elif category == "tutor":
        people = contacts.get("tutors", [])
        color = "#34a853"
        label = "Tutor"
    elif category == "job":
        people = contacts.get("job_contacts", [])
        color = "#fbbc04"
        label = "Job Contact"
    else:
        return None

    available = [p for p in people if p.get("user_id")]
    if not available:
        return None

    if len(available) == 1:
        return None  # Will auto-connect

    lines = []
    for i, p in enumerate(available, 1):
        extra = ""
        if category == "tutor":
            extra = " (" + ", ".join(p.get("subjects", [])) + ")"
        elif category == "job":
            extra = " - " + p.get("company", "")
        lines.append(str(i) + ". " + p["name"] + " - " + p.get("role", "") + extra)

    text = "Choose who to talk to:\n\n" + "\n".join(lines) + "\n\nReply with the number."
    return text


def build_scholarship_response(contacts):
    info = contacts.get("scholarship", {})
    flex_json = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "Scholarship Support", "size": "lg", "weight": "bold", "color": "#ea4335"},
                {"type": "text", "text": info.get("description", ""), "size": "sm", "color": "#666666", "margin": "lg", "wrap": True},
                {"type": "separator", "margin": "xl"},
                {"type": "text", "text": "Contact: " + info.get("contact_name", "Ethan"), "size": "sm", "margin": "lg"},
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
                    "action": {"type": "uri", "label": "Fill Scholarship Form", "uri": info.get("google_form_url", "https://docs.google.com/forms")},
                    "style": "primary",
                    "color": "#ea4335",
                },
                {
                    "type": "button",
                    "action": {"type": "uri", "label": "View Scholarship Document", "uri": info.get("google_doc_url", "https://docs.google.com/document")},
                    "style": "secondary",
                },
            ],
            "paddingAll": "12px",
        },
    }

    messages = [
        TextSendMessage(text="Here is the scholarship information. Fill in the form to get started!"),
        FlexSendMessage(alt_text="Scholarship info", contents=flex_json),
    ]

    # Also offer to connect with scholarship contact
    contact_id = info.get("contact_user_id", "")
    if contact_id:
        messages.append(TextSendMessage(text="Want to talk to " + info.get("contact_name", "someone") + " about scholarships? Type 'connect' to start a conversation."))

    return messages


# ─── Connection Logic ────────────────────────────────────────────

def connect_users(student_id, helper_id, helper_name, category, sessions):
    """Create a two-way connection between student and helper."""
    student_name = get_display_name(student_id)

    sessions[student_id] = {
        "connected_to": helper_id,
        "connected_name": helper_name,
        "category": category,
        "started": int(time.time()),
    }
    sessions[helper_id] = {
        "connected_to": student_id,
        "connected_name": student_name,
        "category": "responding",
        "started": int(time.time()),
    }
    save_sessions(sessions)

    # Notify the student
    line_bot_api.push_message(
        student_id,
        TextSendMessage(
            text="You are now connected with " + helper_name + "!\n\n"
            "Type your message and I will forward it to them.\n"
            "Type 'exit' to end the conversation and return to the menu."
        ),
    )

    # Notify the helper
    category_label = category
    if category == "counselor":
        category_label = "counseling/admissions"
    elif category == "tutor":
        category_label = "education/test support"
    elif category == "job":
        category_label = "job search"
    elif category == "scholarship":
        category_label = "scholarship"

    line_bot_api.push_message(
        helper_id,
        TextSendMessage(
            text="New conversation!\n\n"
            + student_name + " needs help with " + category_label + ".\n\n"
            "Their messages will appear here. Just reply normally and I will forward your response.\n"
            "Type 'exit' to end the conversation."
        ),
    )


def disconnect_users(user_id, sessions):
    """End a conversation between two users."""
    session = sessions.get(user_id)
    if not session:
        return

    other_id = session["connected_to"]
    other_name = session["connected_name"]
    my_name = get_display_name(user_id)

    # Notify the other person
    try:
        line_bot_api.push_message(
            other_id,
            [
                TextSendMessage(text="The conversation with " + my_name + " has ended."),
                TextSendMessage(text="Type 'hi' to return to the menu."),
            ],
        )
    except Exception:
        pass

    # Remove both sessions
    sessions.pop(user_id, None)
    sessions.pop(other_id, None)
    save_sessions(sessions)


def get_available_people(category, contacts):
    """Get list of people with registered user_ids for a category."""
    if category == "counselor":
        return [p for p in contacts.get("counselors", []) if p.get("user_id")]
    elif category == "tutor":
        return [p for p in contacts.get("tutors", []) if p.get("user_id")]
    elif category == "job":
        return [p for p in contacts.get("job_contacts", []) if p.get("user_id")]
    elif category == "scholarship":
        uid = contacts.get("scholarship", {}).get("contact_user_id", "")
        name = contacts.get("scholarship", {}).get("contact_name", "")
        if uid:
            return [{"name": name, "user_id": uid}]
        return []
    return []


# ─── Admin Commands ──────────────────────────────────────────────

ADMIN_HELP = """Admin Commands:

REGISTER (helpers must message the bot first):
/register counselor <name>
/register tutor <name>
/register job <name>
/register scholarship

This links YOUR LINE account as that person. The helper must have messaged the bot at least once.

ADD PEOPLE:
/add counselor Name | Role | email
/add tutor Name | Role | Subject1, Subject2
/add job Name | Company | Role | Industry

MANAGE:
/remove counselor Name
/remove tutor Name
/remove job Name
/set scholarship form <url>
/set scholarship doc <url>
/add admin <user_id>
/list admins
/list sessions
/my id

Example workflow:
1. /add counselor Khun Nida | University Admissions | nida@ris.ac.th
2. Tell Khun Nida to add the bot as a friend and send 'hi'
3. Khun Nida sends: /register counselor Khun Nida
4. Now students who pick option 1 get connected to Khun Nida!"""


def handle_admin_command(user_id, text):
    contacts = load_contacts()
    sessions = load_sessions()
    admin_ids = contacts.get("admin_ids", [])

    # First user becomes admin
    if not admin_ids:
        contacts["admin_ids"] = [user_id]
        save_contacts(contacts)
        admin_ids = [user_id]

    text_lower = text.lower().strip()

    # /my id — available to everyone
    if text_lower == "/my id":
        return "Your LINE user ID is:\n" + user_id

    # /register — available to everyone (they register themselves)
    if text_lower.startswith("/register "):
        return handle_register(user_id, text, contacts)

    # Everything else requires admin
    if user_id not in admin_ids:
        return "You don't have admin access.\nYour user ID: " + user_id + "\nAsk an admin to run: /add admin " + user_id

    if text_lower in ["/admin", "/help"]:
        return ADMIN_HELP

    if text_lower == "/list admins":
        return "Admin IDs:\n" + "\n".join(admin_ids) if admin_ids else "No admins."

    if text_lower == "/list sessions":
        if not sessions:
            return "No active conversations."
        lines = []
        seen = set()
        for uid, s in sessions.items():
            pair = tuple(sorted([uid, s["connected_to"]]))
            if pair not in seen:
                seen.add(pair)
                lines.append(s.get("connected_name", "?") + " <-> " + get_display_name(uid) + " (" + s.get("category", "?") + ")")
        return "Active conversations:\n" + "\n".join(lines)

    if text_lower.startswith("/add admin "):
        new_id = text[11:].strip()
        if new_id not in contacts["admin_ids"]:
            contacts["admin_ids"].append(new_id)
            save_contacts(contacts)
        return "Added admin: " + new_id

    if text_lower.startswith("/add counselor "):
        parts = text[15:].split("|")
        if len(parts) < 3:
            return "Format: /add counselor Name | Role | Email"
        entry = {"name": parts[0].strip(), "role": parts[1].strip(), "email": parts[2].strip(), "user_id": ""}
        contacts["counselors"].append(entry)
        save_contacts(contacts)
        return "Added counselor: " + entry["name"] + "\nThey need to message the bot and run: /register counselor " + entry["name"]

    if text_lower.startswith("/add tutor "):
        parts = text[11:].split("|")
        if len(parts) < 3:
            return "Format: /add tutor Name | Role | Subjects"
        entry = {"name": parts[0].strip(), "role": parts[1].strip(), "user_id": "", "subjects": [s.strip() for s in parts[2].split(",")]}
        contacts["tutors"].append(entry)
        save_contacts(contacts)
        return "Added tutor: " + entry["name"] + "\nThey need to message the bot and run: /register tutor " + entry["name"]

    if text_lower.startswith("/add job "):
        parts = text[9:].split("|")
        if len(parts) < 4:
            return "Format: /add job Name | Company | Role | Industry"
        entry = {"name": parts[0].strip(), "company": parts[1].strip(), "role": parts[2].strip(), "user_id": "", "industry": parts[3].strip()}
        contacts["job_contacts"].append(entry)
        save_contacts(contacts)
        return "Added job contact: " + entry["name"] + "\nThey need to message the bot and run: /register job " + entry["name"]

    if text_lower.startswith("/remove counselor "):
        name = text[18:].strip()
        before = len(contacts["counselors"])
        contacts["counselors"] = [c for c in contacts["counselors"] if c["name"].lower() != name.lower()]
        save_contacts(contacts)
        return ("Removed: " + name) if len(contacts["counselors"]) < before else ("Not found: " + name)

    if text_lower.startswith("/remove tutor "):
        name = text[14:].strip()
        before = len(contacts["tutors"])
        contacts["tutors"] = [t for t in contacts["tutors"] if t["name"].lower() != name.lower()]
        save_contacts(contacts)
        return ("Removed: " + name) if len(contacts["tutors"]) < before else ("Not found: " + name)

    if text_lower.startswith("/remove job "):
        name = text[12:].strip()
        before = len(contacts["job_contacts"])
        contacts["job_contacts"] = [j for j in contacts["job_contacts"] if j["name"].lower() != name.lower()]
        save_contacts(contacts)
        return ("Removed: " + name) if len(contacts["job_contacts"]) < before else ("Not found: " + name)

    if text_lower.startswith("/set scholarship form "):
        contacts["scholarship"]["google_form_url"] = text[22:].strip()
        save_contacts(contacts)
        return "Scholarship form URL updated."

    if text_lower.startswith("/set scholarship doc "):
        contacts["scholarship"]["google_doc_url"] = text[21:].strip()
        save_contacts(contacts)
        return "Scholarship doc URL updated."

    return "Unknown command. Type /admin for help."


def handle_register(user_id, text, contacts):
    """Let a helper register their LINE account to their name in the contacts list."""
    text_lower = text.lower().strip()

    if text_lower.startswith("/register counselor "):
        name = text[20:].strip()
        for c in contacts["counselors"]:
            if c["name"].lower() == name.lower():
                c["user_id"] = user_id
                save_contacts(contacts)
                return "Registered! You (" + name + ") are now linked as a counselor.\nWhen students need counseling help, their messages will be forwarded to you here."
        return "No counselor named '" + name + "' found. Ask an admin to add you first with /add counselor"

    if text_lower.startswith("/register tutor "):
        name = text[16:].strip()
        for t in contacts["tutors"]:
            if t["name"].lower() == name.lower():
                t["user_id"] = user_id
                save_contacts(contacts)
                return "Registered! You (" + name + ") are now linked as a tutor.\nWhen students need study help, their messages will be forwarded to you here."
        return "No tutor named '" + name + "' found. Ask an admin to add you first with /add tutor"

    if text_lower.startswith("/register job "):
        name = text[14:].strip()
        for j in contacts["job_contacts"]:
            if j["name"].lower() == name.lower():
                j["user_id"] = user_id
                save_contacts(contacts)
                return "Registered! You (" + name + ") are now linked as a job contact.\nWhen students need career help, their messages will be forwarded to you here."
        return "No job contact named '" + name + "' found. Ask an admin to add you first with /add job"

    if text_lower == "/register scholarship":
        contacts["scholarship"]["contact_user_id"] = user_id
        save_contacts(contacts)
        return "Registered! You are now the scholarship contact.\nWhen students need scholarship help, their messages will be forwarded to you here."

    return "Usage:\n/register counselor YourName\n/register tutor YourName\n/register job YourName\n/register scholarship"


# ─── Pending state: waiting to pick a person ─────────────────────
# We store a lightweight "pending" state for when there are multiple
# people in a category and the student needs to pick one.

PENDING_FILE = os.path.join(DATA_DIR, "pending.json")


def load_pending():
    if os.path.exists(PENDING_FILE):
        with open(PENDING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_pending(data):
    with open(PENDING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ─── Main Message Handler ───────────────────────────────────────

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
    text_lower = text.lower()

    sessions = load_sessions()
    contacts = load_contacts()
    pending = load_pending()

    # ── 1. Admin/register commands (always available) ──
    if text.startswith("/"):
        # But first disconnect if in session
        if user_id in sessions and text_lower not in ["/my id"]:
            disconnect_users(user_id, sessions)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="Conversation ended.\n\n" + handle_admin_command(user_id, text)),
            )
            return

        reply = handle_admin_command(user_id, text)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    # ── 2. If user is in an active conversation, relay the message ──
    if user_id in sessions:
        if text_lower == "exit":
            other_name = sessions[user_id]["connected_name"]
            disconnect_users(user_id, sessions)
            line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text="Conversation with " + other_name + " ended."),
                    TextSendMessage(text="Type 'hi' to return to the menu."),
                ],
            )
            return

        # Forward the message to the other person
        other_id = sessions[user_id]["connected_to"]
        sender_name = get_display_name(user_id)
        try:
            line_bot_api.push_message(
                other_id,
                TextSendMessage(text=sender_name + ":\n" + text),
            )
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="(sent)"),
            )
        except Exception as e:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="Could not deliver message. The other person may not have added the bot yet. Error: " + str(e)[:100]),
            )
        return

    # ── 3. If user is picking from a list of people ──
    if user_id in pending:
        category = pending[user_id]["category"]
        available = get_available_people(category, contacts)

        try:
            choice = int(text) - 1
            if 0 <= choice < len(available):
                person = available[choice]
                # Check if helper is already in a conversation
                if person["user_id"] in sessions:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=person["name"] + " is currently helping someone else. Please try again in a few minutes, or pick another person."),
                    )
                    return

                del pending[user_id]
                save_pending(pending)
                connect_users(user_id, person["user_id"], person["name"], category, sessions)
                # reply already sent by connect_users via push
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="Connecting you to " + person["name"] + "..."))
                return
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="Please pick a valid number from the list, or type 'exit' to go back."))
                return
        except ValueError:
            if text_lower == "exit":
                del pending[user_id]
                save_pending(pending)
                line_bot_api.reply_message(event.reply_token, build_main_menu())
                return
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="Please reply with a number, or type 'exit' to go back."))
            return

    # ── 4. Menu triggers ──
    if text_lower in ["hi", "hello", "menu", "start", "help", "hey", "back"]:
        line_bot_api.reply_message(event.reply_token, build_main_menu())
        return

    # ── 5. Option routing ──

    def try_connect(category):
        available = get_available_people(category, contacts)
        if not available:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="Sorry, no one is available for this category right now. All helpers need to register with the bot first.\n\nType 'hi' to return to the menu."),
            )
            return

        if len(available) == 1:
            person = available[0]
            if person["user_id"] in sessions:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=person["name"] + " is currently helping someone else. Please try again in a few minutes."),
                )
                return
            connect_users(user_id, person["user_id"], person["name"], category, sessions)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="Connecting you to " + person["name"] + "..."))
            return

        # Multiple people available — ask to pick
        picker_text = build_person_picker(category, contacts)
        if picker_text:
            pending[user_id] = {"category": category}
            save_pending(pending)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=picker_text))
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="Sorry, no registered helpers available right now."),
            )

    # Option 1: Counselor
    if text in ["1"] or "counselor" in text_lower or "admission" in text_lower:
        try_connect("counselor")
        return

    # Option 2: Education
    if text in ["2"] or "tutor" in text_lower or "education" in text_lower or "test" in text_lower or "study" in text_lower:
        try_connect("tutor")
        return

    # Option 3: Scholarship
    if text in ["3"] or "scholarship" in text_lower:
        messages = build_scholarship_response(contacts)
        line_bot_api.reply_message(event.reply_token, messages)
        return

    # Option 3 follow-up: connect to scholarship contact
    if text_lower == "connect":
        scholarship_id = contacts.get("scholarship", {}).get("contact_user_id", "")
        scholarship_name = contacts.get("scholarship", {}).get("contact_name", "")
        if scholarship_id:
            if scholarship_id in sessions:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=scholarship_name + " is currently helping someone else. Try again shortly."),
                )
                return
            connect_users(user_id, scholarship_id, scholarship_name, "scholarship", sessions)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="Connecting you to " + scholarship_name + "..."))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="Scholarship contact hasn't registered yet. Please fill in the form in the meantime!"))
        return

    # Option 4: Job
    if text in ["4"] or "job" in text_lower or "work" in text_lower or "career" in text_lower:
        try_connect("job")
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
