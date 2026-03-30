"""
LINE Chatbot — Student Support Hub v3
Relay system using line-bot-sdk 3.5.1 + Python 3.12
"""

import os
import json
import time
from flask import Flask, request, abort

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    PushMessageRequest,
    TextMessage,
    FlexMessage,
    FlexContainer,
)

app = Flask(__name__)

CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "YOUR_CHANNEL_SECRET")
CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "YOUR_ACCESS_TOKEN")

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
webhook_handler = WebhookHandler(CHANNEL_SECRET)

DATA_DIR = os.path.dirname(__file__)
CONTACTS_FILE = os.path.join(DATA_DIR, "contacts.json")
SESSIONS_FILE = os.path.join(DATA_DIR, "sessions.json")
PENDING_FILE = os.path.join(DATA_DIR, "pending.json")


# ─── File helpers ────────────────────────────────────────────────

def _load(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def _save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_contacts():
    return _load(CONTACTS_FILE, DEFAULT_CONTACTS)

def save_contacts(data):
    _save(CONTACTS_FILE, data)

def load_sessions():
    return _load(SESSIONS_FILE, {})

def save_sessions(data):
    _save(SESSIONS_FILE, data)

def load_pending():
    return _load(PENDING_FILE, {})

def save_pending(data):
    _save(PENDING_FILE, data)


DEFAULT_CONTACTS = {
    "counselors": [
        {"name": "Khun Somporn", "role": "Admissions & Academic Guidance", "user_id": "", "email": "somporn@school.ac.th"}
    ],
    "tutors": [
        {"name": "Ethan", "role": "Team Lead - General Support", "user_id": "", "subjects": ["Math", "Science", "English"]}
    ],
    "scholarship": {
        "contact_name": "Ethan",
        "contact_user_id": "",
        "google_form_url": "https://docs.google.com/forms/d/e/YOUR_FORM_ID/viewform",
        "google_doc_url": "https://docs.google.com/document/d/YOUR_DOC_ID/edit",
        "description": "We offer guidance on scholarships for students at risk of dropping out. Fill in the form and we will match you with opportunities.",
    },
    "job_contacts": [
        {"name": "Job Fair Contact", "company": "Company Name", "role": "HR / Recruiter", "user_id": "", "industry": "Technology"}
    ],
    "admin_ids": [],
}

if not os.path.exists(CONTACTS_FILE):
    save_contacts(DEFAULT_CONTACTS)


# ─── Messaging helpers ──────────────────────────────────────────

def get_api():
    return MessagingApi(ApiClient(configuration))

def reply(token, messages):
    if not isinstance(messages, list):
        messages = [messages]
    get_api().reply_message(ReplyMessageRequest(reply_token=token, messages=messages))

def push(user_id, messages):
    if not isinstance(messages, list):
        messages = [messages]
    get_api().push_message(PushMessageRequest(to=user_id, messages=messages))

def text_msg(t):
    return TextMessage(text=t)

def get_display_name(user_id):
    try:
        profile = get_api().get_profile(user_id)
        return profile.display_name
    except Exception:
        return "Someone"


# ─── Flex builders ───────────────────────────────────────────────

def build_main_menu():
    flex_json = {
        "type": "bubble",
        "hero": {
            "type": "box", "layout": "vertical",
            "contents": [
                {"type": "text", "text": "Student Support Hub", "weight": "bold", "size": "xl", "color": "#1a73e8", "align": "center"},
                {"type": "text", "text": "How can we help you today?", "size": "sm", "color": "#666666", "align": "center", "margin": "md"},
            ],
            "paddingAll": "20px", "backgroundColor": "#f0f6ff",
        },
        "body": {
            "type": "box", "layout": "vertical", "spacing": "md",
            "contents": [
                _btn("1 - Talk to a Counselor", "#1a73e8"),
                _btn("2 - Get Education & Test Help", "#34a853"),
                _btn("3 - Scholarship Information", "#ea4335"),
                _btn("4 - Job Search Help", "#fbbc04"),
            ],
            "paddingAll": "16px",
        },
        "footer": {
            "type": "box", "layout": "vertical",
            "contents": [{"type": "text", "text": "Reply 1-4 to connect with someone who can help", "size": "xs", "color": "#999999", "align": "center", "wrap": True}],
            "paddingAll": "12px",
        },
    }
    return FlexMessage(alt_text="Student Support Hub - Reply 1-4", contents=FlexContainer.from_dict(flex_json))

def _btn(label, color):
    return {
        "type": "box", "layout": "horizontal",
        "contents": [{"type": "text", "text": label, "size": "md", "color": "#333333", "flex": 1, "gravity": "center"}],
        "paddingAll": "14px", "backgroundColor": "#ffffff", "cornerRadius": "8px", "borderWidth": "1px", "borderColor": color,
    }

def build_scholarship_messages(contacts):
    info = contacts.get("scholarship", {})
    flex_json = {
        "type": "bubble",
        "body": {
            "type": "box", "layout": "vertical",
            "contents": [
                {"type": "text", "text": "Scholarship Support", "size": "lg", "weight": "bold", "color": "#ea4335"},
                {"type": "text", "text": info.get("description", ""), "size": "sm", "color": "#666666", "margin": "lg", "wrap": True},
                {"type": "separator", "margin": "xl"},
                {"type": "text", "text": "Contact: " + info.get("contact_name", "Ethan"), "size": "sm", "margin": "lg"},
            ],
            "paddingAll": "20px",
        },
        "footer": {
            "type": "box", "layout": "vertical", "spacing": "sm",
            "contents": [
                {"type": "button", "action": {"type": "uri", "label": "Fill Scholarship Form", "uri": info.get("google_form_url", "https://docs.google.com/forms")}, "style": "primary", "color": "#ea4335"},
                {"type": "button", "action": {"type": "uri", "label": "View Scholarship Document", "uri": info.get("google_doc_url", "https://docs.google.com/document")}, "style": "secondary"},
            ],
            "paddingAll": "12px",
        },
    }
    msgs = [
        text_msg("Here is the scholarship information. Fill in the form to get started!"),
        FlexMessage(alt_text="Scholarship info", contents=FlexContainer.from_dict(flex_json)),
    ]
    if info.get("contact_user_id"):
        msgs.append(text_msg("Want to talk to " + info.get("contact_name", "someone") + " about scholarships? Type 'connect' to start a conversation."))
    return msgs


# ─── Connection logic ────────────────────────────────────────────

def get_available(category, contacts):
    if category == "counselor":
        return [p for p in contacts.get("counselors", []) if p.get("user_id")]
    elif category == "tutor":
        return [p for p in contacts.get("tutors", []) if p.get("user_id")]
    elif category == "job":
        return [p for p in contacts.get("job_contacts", []) if p.get("user_id")]
    elif category == "scholarship":
        uid = contacts.get("scholarship", {}).get("contact_user_id", "")
        name = contacts.get("scholarship", {}).get("contact_name", "")
        return [{"name": name, "user_id": uid}] if uid else []
    return []

def connect_users(student_id, helper_id, helper_name, category, sessions):
    student_name = get_display_name(student_id)
    sessions[student_id] = {"connected_to": helper_id, "connected_name": helper_name, "category": category, "started": int(time.time())}
    sessions[helper_id] = {"connected_to": student_id, "connected_name": student_name, "category": "responding", "started": int(time.time())}
    save_sessions(sessions)

    push(student_id, text_msg(
        "You are now connected with " + helper_name + "!\n\n"
        "Type your message and I will forward it to them.\n"
        "Type 'exit' to end the conversation and return to the menu."
    ))

    label = {"counselor": "counseling/admissions", "tutor": "education/test support", "job": "job search", "scholarship": "scholarship"}.get(category, category)
    push(helper_id, text_msg(
        "New conversation!\n\n"
        + student_name + " needs help with " + label + ".\n\n"
        "Their messages will appear here. Just reply normally and I will forward your response.\n"
        "Type 'exit' to end the conversation."
    ))

def disconnect_users(user_id, sessions):
    session = sessions.get(user_id)
    if not session:
        return
    other_id = session["connected_to"]
    my_name = get_display_name(user_id)
    try:
        push(other_id, [text_msg("The conversation with " + my_name + " has ended."), text_msg("Type 'hi' to return to the menu.")])
    except Exception:
        pass
    sessions.pop(user_id, None)
    sessions.pop(other_id, None)
    save_sessions(sessions)

def build_picker(category, contacts):
    available = get_available(category, contacts)
    if len(available) <= 1:
        return None
    lines = []
    for i, p in enumerate(available, 1):
        extra = ""
        if category == "tutor":
            extra = " (" + ", ".join(p.get("subjects", [])) + ")"
        elif category == "job":
            extra = " - " + p.get("company", "")
        lines.append(str(i) + ". " + p["name"] + " - " + p.get("role", "") + extra)
    return "Choose who to talk to:\n\n" + "\n".join(lines) + "\n\nReply with the number, or 'exit' to go back."


# ─── Admin commands ──────────────────────────────────────────────

ADMIN_HELP = """Admin Commands:

REGISTER (helpers message bot first):
/register counselor YourName
/register tutor YourName
/register job YourName
/register scholarship

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
/my id"""

def handle_admin(user_id, text):
    contacts = load_contacts()
    sessions = load_sessions()
    admin_ids = contacts.get("admin_ids", [])
    if not admin_ids:
        contacts["admin_ids"] = [user_id]
        save_contacts(contacts)
        admin_ids = [user_id]

    tl = text.lower().strip()

    if tl == "/my id":
        return "Your LINE user ID:\n" + user_id

    if tl.startswith("/register "):
        return handle_register(user_id, text, contacts)

    if user_id not in admin_ids:
        return "No admin access.\nYour ID: " + user_id + "\nAsk admin to run: /add admin " + user_id

    if tl in ["/admin", "/help"]:
        return ADMIN_HELP
    if tl == "/list admins":
        return "Admins:\n" + "\n".join(admin_ids) if admin_ids else "None."
    if tl == "/list sessions":
        if not sessions:
            return "No active conversations."
        seen, lines = set(), []
        for uid, s in sessions.items():
            pair = tuple(sorted([uid, s["connected_to"]]))
            if pair not in seen:
                seen.add(pair)
                lines.append(s.get("connected_name", "?") + " <-> " + get_display_name(uid))
        return "Active:\n" + "\n".join(lines)

    if tl.startswith("/add admin "):
        nid = text[11:].strip()
        if nid not in contacts["admin_ids"]:
            contacts["admin_ids"].append(nid)
            save_contacts(contacts)
        return "Added admin: " + nid

    if tl.startswith("/add counselor "):
        parts = text[15:].split("|")
        if len(parts) < 3:
            return "Format: /add counselor Name | Role | Email"
        e = {"name": parts[0].strip(), "role": parts[1].strip(), "email": parts[2].strip(), "user_id": ""}
        contacts["counselors"].append(e)
        save_contacts(contacts)
        return "Added: " + e["name"] + "\nThey must message bot then: /register counselor " + e["name"]

    if tl.startswith("/add tutor "):
        parts = text[11:].split("|")
        if len(parts) < 3:
            return "Format: /add tutor Name | Role | Subjects"
        e = {"name": parts[0].strip(), "role": parts[1].strip(), "user_id": "", "subjects": [s.strip() for s in parts[2].split(",")]}
        contacts["tutors"].append(e)
        save_contacts(contacts)
        return "Added: " + e["name"] + "\nThey must message bot then: /register tutor " + e["name"]

    if tl.startswith("/add job "):
        parts = text[9:].split("|")
        if len(parts) < 4:
            return "Format: /add job Name | Company | Role | Industry"
        e = {"name": parts[0].strip(), "company": parts[1].strip(), "role": parts[2].strip(), "user_id": "", "industry": parts[3].strip()}
        contacts["job_contacts"].append(e)
        save_contacts(contacts)
        return "Added: " + e["name"] + "\nThey must message bot then: /register job " + e["name"]

    if tl.startswith("/remove counselor "):
        n = text[18:].strip()
        b = len(contacts["counselors"])
        contacts["counselors"] = [c for c in contacts["counselors"] if c["name"].lower() != n.lower()]
        save_contacts(contacts)
        return ("Removed: " + n) if len(contacts["counselors"]) < b else ("Not found: " + n)

    if tl.startswith("/remove tutor "):
        n = text[14:].strip()
        b = len(contacts["tutors"])
        contacts["tutors"] = [t for t in contacts["tutors"] if t["name"].lower() != n.lower()]
        save_contacts(contacts)
        return ("Removed: " + n) if len(contacts["tutors"]) < b else ("Not found: " + n)

    if tl.startswith("/remove job "):
        n = text[12:].strip()
        b = len(contacts["job_contacts"])
        contacts["job_contacts"] = [j for j in contacts["job_contacts"] if j["name"].lower() != n.lower()]
        save_contacts(contacts)
        return ("Removed: " + n) if len(contacts["job_contacts"]) < b else ("Not found: " + n)

    if tl.startswith("/set scholarship form "):
        contacts["scholarship"]["google_form_url"] = text[22:].strip()
        save_contacts(contacts)
        return "Form URL updated."

    if tl.startswith("/set scholarship doc "):
        contacts["scholarship"]["google_doc_url"] = text[21:].strip()
        save_contacts(contacts)
        return "Doc URL updated."

    return "Unknown command. Type /admin for help."

def handle_register(user_id, text, contacts):
    tl = text.lower().strip()
    if tl.startswith("/register counselor "):
        name = text[20:].strip()
        for c in contacts["counselors"]:
            if c["name"].lower() == name.lower():
                c["user_id"] = user_id
                save_contacts(contacts)
                return "Registered! You (" + name + ") will now receive forwarded student messages for counseling."
        return "No counselor named '" + name + "'. Ask admin to add you first."

    if tl.startswith("/register tutor "):
        name = text[16:].strip()
        for t in contacts["tutors"]:
            if t["name"].lower() == name.lower():
                t["user_id"] = user_id
                save_contacts(contacts)
                return "Registered! You (" + name + ") will now receive forwarded student messages for tutoring."
        return "No tutor named '" + name + "'. Ask admin to add you first."

    if tl.startswith("/register job "):
        name = text[14:].strip()
        for j in contacts["job_contacts"]:
            if j["name"].lower() == name.lower():
                j["user_id"] = user_id
                save_contacts(contacts)
                return "Registered! You (" + name + ") will now receive forwarded student messages for job help."
        return "No job contact named '" + name + "'. Ask admin to add you first."

    if tl == "/register scholarship":
        contacts["scholarship"]["contact_user_id"] = user_id
        save_contacts(contacts)
        return "Registered as scholarship contact!"

    return "Usage: /register counselor YourName"


# ─── Main handler ────────────────────────────────────────────────

@app.route("/callback", methods=["POST"])
def callback():
    sig = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        webhook_handler.handle(body, sig)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@webhook_handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    uid = event.source.user_id
    text = event.message.text.strip()
    tl = text.lower()

    sessions = load_sessions()
    contacts = load_contacts()
    pending = load_pending()

    # 1. Commands
    if text.startswith("/"):
        if uid in sessions and tl != "/my id":
            disconnect_users(uid, sessions)
        r = handle_admin(uid, text)
        reply(event.reply_token, text_msg(r))
        return

    # 2. Active conversation — relay
    if uid in sessions:
        if tl == "exit":
            other = sessions[uid]["connected_name"]
            disconnect_users(uid, sessions)
            reply(event.reply_token, [text_msg("Conversation with " + other + " ended."), text_msg("Type 'hi' to return to the menu.")])
            return

        other_id = sessions[uid]["connected_to"]
        sender = get_display_name(uid)
        try:
            push(other_id, text_msg(sender + ":\n" + text))
            reply(event.reply_token, text_msg("(sent)"))
        except Exception as e:
            reply(event.reply_token, text_msg("Could not deliver. Error: " + str(e)[:100]))
        return

    # 3. Picking from list
    if uid in pending:
        cat = pending[uid]["category"]
        avail = get_available(cat, contacts)
        if tl == "exit":
            del pending[uid]
            save_pending(pending)
            reply(event.reply_token, build_main_menu())
            return
        try:
            idx = int(text) - 1
            if 0 <= idx < len(avail):
                p = avail[idx]
                if p["user_id"] in sessions:
                    reply(event.reply_token, text_msg(p["name"] + " is busy. Try again shortly."))
                    return
                del pending[uid]
                save_pending(pending)
                connect_users(uid, p["user_id"], p["name"], cat, sessions)
                reply(event.reply_token, text_msg("Connecting you to " + p["name"] + "..."))
                return
            reply(event.reply_token, text_msg("Pick a valid number or type 'exit'."))
            return
        except ValueError:
            reply(event.reply_token, text_msg("Reply with a number or type 'exit'."))
            return

    # 4. Menu
    if tl in ["hi", "hello", "menu", "start", "help", "hey", "back"]:
        reply(event.reply_token, build_main_menu())
        return

    # 5. Options
    def try_connect(category):
        avail = get_available(category, contacts)
        if not avail:
            reply(event.reply_token, text_msg("No one available for this yet. Helpers need to register first.\nType 'hi' for menu."))
            return
        if len(avail) == 1:
            p = avail[0]
            if p["user_id"] in sessions:
                reply(event.reply_token, text_msg(p["name"] + " is busy. Try again shortly."))
                return
            connect_users(uid, p["user_id"], p["name"], category, sessions)
            reply(event.reply_token, text_msg("Connecting you to " + p["name"] + "..."))
            return
        picker = build_picker(category, contacts)
        if picker:
            pending[uid] = {"category": category}
            save_pending(pending)
            reply(event.reply_token, text_msg(picker))

    if text in ["1"] or "counselor" in tl or "admission" in tl:
        try_connect("counselor")
        return
    if text in ["2"] or "tutor" in tl or "education" in tl or "test" in tl or "study" in tl:
        try_connect("tutor")
        return
    if text in ["3"] or "scholarship" in tl:
        reply(event.reply_token, build_scholarship_messages(contacts))
        return
    if tl == "connect":
        si = contacts.get("scholarship", {})
        sid, sn = si.get("contact_user_id", ""), si.get("contact_name", "")
        if sid:
            if sid in sessions:
                reply(event.reply_token, text_msg(sn + " is busy. Try shortly."))
                return
            connect_users(uid, sid, sn, "scholarship", sessions)
            reply(event.reply_token, text_msg("Connecting you to " + sn + "..."))
        else:
            reply(event.reply_token, text_msg("Scholarship contact not registered yet. Please fill in the form!"))
        return
    if text in ["4"] or "job" in tl or "work" in tl or "career" in tl:
        try_connect("job")
        return

    # Default
    reply(event.reply_token, [text_msg("Welcome! Let me help you find the right support."), build_main_menu()])

@app.route("/", methods=["GET"])
def health():
    return "Student Support Hub Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
