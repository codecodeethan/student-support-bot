"""
LINE Chatbot — Student Support Hub v6
Simple, clean, Instagram DM-style inbox for helpers.
Clear connection flow for students.
"""

import os
import json
import time
from flask import Flask, request, abort

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    ReplyMessageRequest, PushMessageRequest,
    TextMessage, FlexMessage, FlexContainer,
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

def _load(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def _save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_contacts(): return _load(CONTACTS_FILE, DEFAULT_CONTACTS)
def save_contacts(d): _save(CONTACTS_FILE, d)
def load_sessions(): return _load(SESSIONS_FILE, {})
def save_sessions(d): _save(SESSIONS_FILE, d)
def load_pending(): return _load(PENDING_FILE, {})
def save_pending(d): _save(PENDING_FILE, d)

DEFAULT_CONTACTS = {
    "counselors": [{"name": "Khun Somporn", "role": "Admissions & Guidance", "user_id": "", "email": "somporn@school.ac.th"}],
    "tutors": [{"name": "Ethan", "role": "Team Lead", "user_id": "", "subjects": ["Math", "Science", "English"]}],
    "scholarship": {
        "contact_name": "Ethan", "contact_user_id": "",
        "google_form_url": "https://docs.google.com/forms/d/e/YOUR_FORM_ID/viewform",
        "google_doc_url": "https://docs.google.com/document/d/YOUR_DOC_ID/edit",
        "description": "We help students find scholarships. Fill in the form and we will match you with opportunities.",
    },
    "job_contacts": [{"name": "Job Fair Contact", "company": "Company Name", "role": "HR", "user_id": "", "industry": "Technology"}],
    "admin_ids": [],
}
if not os.path.exists(CONTACTS_FILE):
    save_contacts(DEFAULT_CONTACTS)


# ─── Helpers ─────────────────────────────────────────────────────

def get_api(): return MessagingApi(ApiClient(configuration))

def reply(token, msgs):
    if not isinstance(msgs, list): msgs = [msgs]
    get_api().reply_message(ReplyMessageRequest(reply_token=token, messages=msgs))

def push(uid, msgs):
    if not isinstance(msgs, list): msgs = [msgs]
    get_api().push_message(PushMessageRequest(to=uid, messages=msgs))

def T(t): return TextMessage(text=t)
def F(alt, d): return FlexMessage(alt_text=alt, contents=FlexContainer.from_dict(d))

def get_name(uid):
    try: return get_api().get_profile(uid).display_name
    except: return "Student"

def time_ago(ts):
    d = int(time.time()) - ts
    if d < 60: return "now"
    if d < 3600: return str(d // 60) + "m"
    if d < 86400: return str(d // 3600) + "h"
    return str(d // 86400) + "d"

# Colors
BLUE = "#0066FF"
GREEN = "#00C853"
RED = "#FF3D00"
ORANGE = "#FF9100"
DARK = "#1A1A2E"
GRAY = "#78909C"
LIGHT = "#F5F7FA"
WHITE = "#FFFFFF"

CAT_COLOR = {"counselor": BLUE, "tutor": GREEN, "job": ORANGE, "scholarship": RED}
CAT_LABEL = {"counselor": "Counseling", "tutor": "Education", "job": "Job Search", "scholarship": "Scholarship"}


# ═══════════════════════════════════════════════════════════════
# STUDENT-FACING UI
# ═══════════════════════════════════════════════════════════════

def ui_main_menu():
    return F("Student Support Hub", {
        "type": "bubble", "size": "mega",
        "header": {
            "type": "box", "layout": "vertical", "backgroundColor": DARK, "paddingAll": "22px",
            "contents": [
                {"type": "text", "text": "STUDENT", "size": "xxs", "color": "#FFFFFF60", "weight": "bold"},
                {"type": "text", "text": "Support Hub", "size": "xxl", "color": WHITE, "weight": "bold", "margin": "xs"},
                {"type": "text", "text": "Choose an option to get connected", "size": "xs", "color": "#FFFFFF80", "margin": "md"},
            ],
        },
        "body": {
            "type": "box", "layout": "vertical", "spacing": "md", "paddingAll": "18px",
            "contents": [
                _option_row("1", "Counselor", "Admissions & academic help", BLUE),
                _option_row("2", "Education", "Tutoring & test support", GREEN),
                _option_row("3", "Scholarships", "Financial aid & forms", RED),
                _option_row("4", "Job Search", "Career & job contacts", ORANGE),
            ],
        },
    })

def _option_row(num, title, desc, color):
    return {
        "type": "box", "layout": "horizontal", "spacing": "lg",
        "cornerRadius": "12px", "paddingAll": "14px",
        "borderWidth": "1px", "borderColor": "#E8E8E8",
        "contents": [
            {"type": "box", "layout": "vertical", "width": "40px", "height": "40px",
             "backgroundColor": color, "cornerRadius": "20px",
             "justifyContent": "center", "alignItems": "center",
             "contents": [{"type": "text", "text": num, "color": WHITE, "weight": "bold", "size": "md", "align": "center"}]},
            {"type": "box", "layout": "vertical", "flex": 1,
             "contents": [
                 {"type": "text", "text": title, "weight": "bold", "size": "md", "color": "#1A1A1A"},
                 {"type": "text", "text": desc, "size": "xs", "color": GRAY, "margin": "xs"},
             ]},
        ],
    }


def ui_connecting(helper_name, category):
    color = CAT_COLOR.get(category, BLUE)
    label = CAT_LABEL.get(category, "Support")
    return F("Connecting...", {
        "type": "bubble", "size": "mega",
        "body": {
            "type": "box", "layout": "vertical", "paddingAll": "24px", "spacing": "lg",
            "alignItems": "center",
            "contents": [
                # Loading indicator
                {"type": "box", "layout": "vertical", "width": "60px", "height": "60px",
                 "backgroundColor": color, "cornerRadius": "30px",
                 "justifyContent": "center", "alignItems": "center",
                 "contents": [{"type": "text", "text": helper_name[0].upper(), "color": WHITE, "weight": "bold", "size": "xxl", "align": "center"}]},
                {"type": "text", "text": "Connecting you to", "size": "sm", "color": GRAY, "align": "center"},
                {"type": "text", "text": helper_name, "size": "xl", "weight": "bold", "color": "#1A1A1A", "align": "center"},
                {"type": "box", "layout": "horizontal", "spacing": "sm",
                 "backgroundColor": color + "15", "cornerRadius": "20px",
                 "paddingStart": "14px", "paddingEnd": "14px", "paddingTop": "6px", "paddingBottom": "6px",
                 "contents": [{"type": "text", "text": label, "size": "xs", "color": color, "weight": "bold"}]},
                {"type": "separator", "color": "#E8E8E8"},
                {"type": "text", "text": "Your messages will be forwarded directly. They will reply through this chat.", "size": "sm", "color": GRAY, "wrap": True, "align": "center"},
            ],
        },
        "footer": {
            "type": "box", "layout": "vertical", "paddingAll": "14px", "backgroundColor": LIGHT,
            "contents": [{"type": "text", "text": "Type 'exit' anytime to end the conversation", "size": "xxs", "color": GRAY, "align": "center"}],
        },
    })


def ui_connected(helper_name):
    return F("Connected!", {
        "type": "bubble", "size": "kilo",
        "body": {
            "type": "box", "layout": "horizontal", "paddingAll": "14px", "spacing": "md",
            "backgroundColor": "#E8F5E9", "cornerRadius": "12px",
            "contents": [
                {"type": "box", "layout": "vertical", "width": "8px", "height": "8px",
                 "backgroundColor": GREEN, "cornerRadius": "4px", "margin": "sm"},
                {"type": "text", "text": "Connected to " + helper_name + " — start typing!", "size": "xs", "color": "#2E7D32", "weight": "bold", "flex": 1, "gravity": "center", "wrap": True},
            ],
        },
    })


def ui_sent():
    return F("Sent", {
        "type": "bubble", "size": "kilo",
        "body": {
            "type": "box", "layout": "horizontal", "paddingAll": "10px", "spacing": "sm",
            "contents": [
                {"type": "text", "text": "Delivered", "size": "xxs", "color": GREEN, "weight": "bold", "align": "end", "flex": 1},
            ],
        },
    })


def ui_ended(name):
    return F("Ended", {
        "type": "bubble", "size": "kilo",
        "body": {
            "type": "box", "layout": "vertical", "paddingAll": "16px",
            "backgroundColor": LIGHT, "cornerRadius": "12px",
            "contents": [
                {"type": "text", "text": "Chat with " + name + " ended", "size": "sm", "color": GRAY, "align": "center"},
                {"type": "text", "text": "Type 'hi' to start over", "size": "xxs", "color": "#B0B0B0", "align": "center", "margin": "sm"},
            ],
        },
    })


def ui_picker(category, contacts):
    avail = get_available(category, contacts)
    if len(avail) <= 1: return None
    color = CAT_COLOR.get(category, BLUE)
    label = {"counselor": "Counselors", "tutor": "Tutors", "job": "Job Contacts"}.get(category, "People")

    rows = []
    for i, p in enumerate(avail, 1):
        sub = p.get("role", "")
        if category == "tutor" and p.get("subjects"): sub = ", ".join(p["subjects"])
        if category == "job" and p.get("company"): sub = p["company"]
        rows.append({
            "type": "box", "layout": "horizontal", "spacing": "md",
            "cornerRadius": "10px", "paddingAll": "12px",
            "borderWidth": "1px", "borderColor": "#E8E8E8",
            "contents": [
                {"type": "box", "layout": "vertical", "width": "32px", "height": "32px",
                 "backgroundColor": color, "cornerRadius": "16px",
                 "justifyContent": "center", "alignItems": "center",
                 "contents": [{"type": "text", "text": str(i), "color": WHITE, "weight": "bold", "size": "sm", "align": "center"}]},
                {"type": "box", "layout": "vertical", "flex": 1,
                 "contents": [
                     {"type": "text", "text": p["name"], "size": "sm", "weight": "bold", "color": "#1A1A1A"},
                     {"type": "text", "text": sub, "size": "xxs", "color": GRAY, "margin": "xs"},
                 ]},
            ],
        })

    return F("Choose", {
        "type": "bubble", "size": "mega",
        "header": {
            "type": "box", "layout": "vertical", "paddingAll": "16px", "backgroundColor": color + "12",
            "contents": [
                {"type": "text", "text": "Available " + label, "size": "md", "weight": "bold", "color": color},
                {"type": "text", "text": "Reply with a number", "size": "xs", "color": GRAY, "margin": "sm"},
            ],
        },
        "body": {"type": "box", "layout": "vertical", "spacing": "sm", "paddingAll": "14px", "contents": rows},
    })


def ui_scholarship(contacts):
    info = contacts.get("scholarship", {})
    msgs = [F("Scholarships", {
        "type": "bubble", "size": "mega",
        "header": {
            "type": "box", "layout": "vertical", "paddingAll": "20px", "backgroundColor": RED,
            "contents": [
                {"type": "text", "text": "SCHOLARSHIPS", "size": "xxs", "color": "#FFFFFF80", "weight": "bold"},
                {"type": "text", "text": "Financial Support", "size": "xl", "color": WHITE, "weight": "bold", "margin": "xs"},
            ],
        },
        "body": {
            "type": "box", "layout": "vertical", "paddingAll": "18px", "spacing": "md",
            "contents": [
                {"type": "text", "text": info.get("description", ""), "size": "sm", "color": GRAY, "wrap": True},
            ],
        },
        "footer": {
            "type": "box", "layout": "vertical", "spacing": "sm", "paddingAll": "14px",
            "contents": [
                {"type": "button", "action": {"type": "uri", "label": "Fill Application Form", "uri": info.get("google_form_url", "https://docs.google.com/forms")}, "style": "primary", "color": RED, "height": "sm"},
                {"type": "button", "action": {"type": "uri", "label": "View Details", "uri": info.get("google_doc_url", "https://docs.google.com/document")}, "style": "secondary", "height": "sm"},
            ],
        },
    })]
    if info.get("contact_user_id"):
        msgs.append(T("Want to discuss scholarships with someone? Type 'connect'"))
    return msgs


# ═══════════════════════════════════════════════════════════════
# HELPER-FACING UI (Instagram DM style)
# ═══════════════════════════════════════════════════════════════

def ui_new_request(student_name, category):
    """Notification that a new student wants to talk."""
    color = CAT_COLOR.get(category, BLUE)
    label = CAT_LABEL.get(category, "Support")
    return F("New request", {
        "type": "bubble", "size": "mega",
        "body": {
            "type": "box", "layout": "vertical", "paddingAll": "20px", "spacing": "md",
            "contents": [
                # Header row
                {"type": "box", "layout": "horizontal", "spacing": "sm",
                 "contents": [
                     {"type": "box", "layout": "vertical", "width": "8px", "height": "8px",
                      "backgroundColor": GREEN, "cornerRadius": "4px", "margin": "sm"},
                     {"type": "text", "text": "NEW REQUEST", "size": "xxs", "color": GREEN, "weight": "bold"},
                 ]},
                # Student info
                {"type": "box", "layout": "horizontal", "spacing": "lg",
                 "contents": [
                     {"type": "box", "layout": "vertical", "width": "48px", "height": "48px",
                      "backgroundColor": color, "cornerRadius": "24px",
                      "justifyContent": "center", "alignItems": "center",
                      "contents": [{"type": "text", "text": student_name[0].upper(), "color": WHITE, "weight": "bold", "size": "xl", "align": "center"}]},
                     {"type": "box", "layout": "vertical", "flex": 1, "justifyContent": "center",
                      "contents": [
                          {"type": "text", "text": student_name, "weight": "bold", "size": "lg", "color": "#1A1A1A"},
                          {"type": "text", "text": label, "size": "xs", "color": color, "weight": "bold", "margin": "xs"},
                      ]},
                 ]},
                {"type": "separator", "color": "#E8E8E8"},
                {"type": "text", "text": "Reply to respond. Your messages are forwarded directly to them.", "size": "xs", "color": GRAY, "wrap": True},
            ],
        },
    })


def ui_student_message(student_name, message, category, is_new_sender=False):
    """A message from a student, shown to the helper."""
    color = CAT_COLOR.get(category, BLUE)
    contents = []

    # Always show who it's from (like Instagram DM header)
    contents.append({
        "type": "box", "layout": "horizontal", "spacing": "sm",
        "contents": [
            {"type": "box", "layout": "vertical", "width": "28px", "height": "28px",
             "backgroundColor": color, "cornerRadius": "14px",
             "justifyContent": "center", "alignItems": "center",
             "contents": [{"type": "text", "text": student_name[0].upper(), "color": WHITE, "weight": "bold", "size": "xs", "align": "center"}]},
            {"type": "text", "text": student_name, "weight": "bold", "size": "sm", "color": "#1A1A1A", "gravity": "center"},
            {"type": "text", "text": "now", "size": "xxs", "color": "#B0B0B0", "gravity": "center", "align": "end", "flex": 1},
        ],
    })

    # Message bubble
    contents.append({
        "type": "box", "layout": "vertical",
        "backgroundColor": LIGHT, "cornerRadius": "16px",
        "paddingAll": "14px", "margin": "sm",
        "contents": [{"type": "text", "text": message, "size": "md", "color": "#1A1A1A", "wrap": True}],
    })

    return F(student_name + ": " + message[:30], {
        "type": "bubble", "size": "mega",
        "body": {"type": "box", "layout": "vertical", "paddingAll": "14px", "spacing": "sm", "contents": contents},
    })


def ui_helper_message(helper_name, message):
    """A message from helper, shown to the student."""
    return F(helper_name + ": " + message[:30], {
        "type": "bubble", "size": "mega",
        "body": {
            "type": "box", "layout": "vertical", "paddingAll": "14px", "spacing": "sm",
            "contents": [
                {"type": "box", "layout": "horizontal", "spacing": "sm",
                 "contents": [
                     {"type": "box", "layout": "vertical", "width": "28px", "height": "28px",
                      "backgroundColor": BLUE, "cornerRadius": "14px",
                      "justifyContent": "center", "alignItems": "center",
                      "contents": [{"type": "text", "text": helper_name[0].upper(), "color": WHITE, "weight": "bold", "size": "xs", "align": "center"}]},
                     {"type": "text", "text": helper_name, "weight": "bold", "size": "sm", "color": "#1A1A1A", "gravity": "center"},
                 ]},
                {"type": "box", "layout": "vertical",
                 "backgroundColor": "#E3F2FD", "cornerRadius": "16px",
                 "paddingAll": "14px", "margin": "sm",
                 "contents": [{"type": "text", "text": message, "size": "md", "color": "#1A1A1A", "wrap": True}]},
            ],
        },
    })


def ui_inbox(helper_session):
    """Instagram-style inbox showing all active conversations."""
    convos = helper_session.get("conversations", {})
    rt = helper_session.get("replying_to")

    if not convos:
        return F("Inbox", {
            "type": "bubble", "size": "mega",
            "body": {"type": "box", "layout": "vertical", "paddingAll": "30px",
                     "contents": [{"type": "text", "text": "No active conversations", "color": GRAY, "align": "center", "size": "sm"}]},
        })

    rows = []
    for sid, info in convos.items():
        is_active = sid == rt
        color = CAT_COLOR.get(info.get("category", "tutor"), GREEN)
        label = CAT_LABEL.get(info.get("category", "tutor"), "Support")
        t = time_ago(info.get("started", int(time.time())))
        last = info.get("last_message", "Tap to reply")

        rows.append({
            "type": "box", "layout": "horizontal", "spacing": "md",
            "paddingAll": "12px", "cornerRadius": "12px",
            "backgroundColor": "#E3F2FD" if is_active else WHITE,
            "borderWidth": "1px", "borderColor": BLUE if is_active else "#E8E8E8",
            "contents": [
                # Avatar
                {"type": "box", "layout": "vertical", "width": "44px", "height": "44px",
                 "backgroundColor": color, "cornerRadius": "22px",
                 "justifyContent": "center", "alignItems": "center",
                 "contents": [
                     {"type": "text", "text": info["name"][0].upper(), "color": WHITE, "weight": "bold", "size": "lg", "align": "center"},
                 ]},
                # Info
                {"type": "box", "layout": "vertical", "flex": 1,
                 "contents": [
                     {"type": "box", "layout": "horizontal",
                      "contents": [
                          {"type": "text", "text": info["name"], "weight": "bold", "size": "sm", "color": "#1A1A1A", "flex": 1},
                          {"type": "text", "text": t, "size": "xxs", "color": "#B0B0B0", "align": "end"},
                      ]},
                     {"type": "box", "layout": "horizontal", "margin": "xs",
                      "contents": [
                          {"type": "text", "text": last if len(last) < 35 else last[:32] + "...", "size": "xs", "color": GRAY, "flex": 1},
                          *([{"type": "box", "layout": "vertical", "width": "18px", "height": "18px",
                              "backgroundColor": BLUE, "cornerRadius": "9px",
                              "justifyContent": "center", "alignItems": "center",
                              "contents": [{"type": "text", "text": "!", "color": WHITE, "size": "xxs", "weight": "bold", "align": "center"}]}] if is_active else []),
                      ]},
                 ]},
            ],
        })

    return F("Inbox", {
        "type": "bubble", "size": "mega",
        "header": {
            "type": "box", "layout": "horizontal", "paddingAll": "16px", "backgroundColor": DARK,
            "contents": [
                {"type": "text", "text": "Inbox", "color": WHITE, "weight": "bold", "size": "lg", "flex": 1},
                {"type": "box", "layout": "vertical", "backgroundColor": BLUE, "cornerRadius": "11px",
                 "width": "22px", "height": "22px", "justifyContent": "center", "alignItems": "center",
                 "contents": [{"type": "text", "text": str(len(convos)), "color": WHITE, "size": "xxs", "weight": "bold", "align": "center"}]},
            ],
        },
        "body": {"type": "box", "layout": "vertical", "spacing": "sm", "paddingAll": "12px", "contents": rows},
        "footer": {
            "type": "box", "layout": "vertical", "paddingAll": "10px", "backgroundColor": LIGHT,
            "contents": [
                {"type": "text", "text": "@Name message = reply to someone", "size": "xxs", "color": GRAY, "align": "center"},
                {"type": "text", "text": "exit Name = end chat", "size": "xxs", "color": GRAY, "align": "center", "margin": "xs"},
            ],
        },
    })


# ═══════════════════════════════════════════════════════════════
# CONNECTION LOGIC
# ═══════════════════════════════════════════════════════════════

def get_available(cat, contacts):
    if cat == "counselor": return [p for p in contacts.get("counselors", []) if p.get("user_id")]
    if cat == "tutor": return [p for p in contacts.get("tutors", []) if p.get("user_id")]
    if cat == "job": return [p for p in contacts.get("job_contacts", []) if p.get("user_id")]
    if cat == "scholarship":
        uid = contacts.get("scholarship", {}).get("contact_user_id", "")
        name = contacts.get("scholarship", {}).get("contact_name", "")
        return [{"name": name, "user_id": uid}] if uid else []
    return []

def connect(student_id, helper_id, helper_name, cat, sessions):
    sname = get_name(student_id)
    sessions[student_id] = {"type": "student", "connected_to": helper_id, "connected_name": helper_name, "category": cat, "started": int(time.time())}
    if helper_id not in sessions or sessions[helper_id].get("type") != "helper":
        sessions[helper_id] = {"type": "helper", "conversations": {}, "replying_to": None}
    sessions[helper_id]["conversations"][student_id] = {"name": sname, "category": cat, "started": int(time.time()), "last_message": "Just connected"}
    sessions[helper_id]["replying_to"] = student_id
    save_sessions(sessions)

    # Student sees: connecting animation + connected confirmation
    push(student_id, [ui_connecting(helper_name, cat), ui_connected(helper_name)])
    # Helper sees: new request card
    push(helper_id, ui_new_request(sname, cat))

def disconnect(student_id, sessions):
    s = sessions.get(student_id)
    if not s or s.get("type") != "student": return
    hid = s["connected_to"]
    sname = get_name(student_id)
    sessions.pop(student_id, None)
    hs = sessions.get(hid)
    if hs and hs.get("type") == "helper":
        hs["conversations"].pop(student_id, None)
        if not hs["conversations"]:
            sessions.pop(hid, None)
            try: push(hid, ui_ended(sname))
            except: pass
        else:
            if hs.get("replying_to") == student_id:
                hs["replying_to"] = list(hs["conversations"].keys())[-1]
            try: push(hid, ui_ended(sname))
            except: pass
    save_sessions(sessions)


# ═══════════════════════════════════════════════════════════════
# ADMIN
# ═══════════════════════════════════════════════════════════════

ADMIN_HELP = """Commands:

/register counselor YourName
/register tutor YourName
/register job YourName
/register scholarship
/add counselor Name | Role | email
/add tutor Name | Role | Subjects
/add job Name | Company | Role | Industry
/remove counselor/tutor/job Name
/set scholarship form <url>
/set scholarship doc <url>
/add admin <user_id>
/my id
/chats"""

def handle_cmd(uid, text):
    contacts = load_contacts()
    admins = contacts.get("admin_ids", [])
    if not admins:
        contacts["admin_ids"] = [uid]; save_contacts(contacts); admins = [uid]
    tl = text.lower().strip()

    if tl == "/my id": return "reply", "Your ID: " + uid
    if tl.startswith("/register "): return "reply", do_register(uid, text, contacts)
    if tl == "/chats": return "chats", None

    if uid not in admins: return "reply", "No admin access. Your ID: " + uid
    if tl in ["/admin", "/help"]: return "reply", ADMIN_HELP
    if tl == "/list admins": return "reply", "Admins:\n" + "\n".join(admins)
    if tl.startswith("/add admin "):
        nid = text[11:].strip()
        if nid not in admins: contacts["admin_ids"].append(nid); save_contacts(contacts)
        return "reply", "Added admin."
    if tl.startswith("/add counselor "):
        p = text[15:].split("|")
        if len(p) < 3: return "reply", "/add counselor Name | Role | Email"
        contacts["counselors"].append({"name": p[0].strip(), "role": p[1].strip(), "email": p[2].strip(), "user_id": ""})
        save_contacts(contacts); return "reply", "Added. They must: /register counselor " + p[0].strip()
    if tl.startswith("/add tutor "):
        p = text[11:].split("|")
        if len(p) < 3: return "reply", "/add tutor Name | Role | Subjects"
        contacts["tutors"].append({"name": p[0].strip(), "role": p[1].strip(), "user_id": "", "subjects": [s.strip() for s in p[2].split(",")]})
        save_contacts(contacts); return "reply", "Added. They must: /register tutor " + p[0].strip()
    if tl.startswith("/add job "):
        p = text[9:].split("|")
        if len(p) < 4: return "reply", "/add job Name | Company | Role | Industry"
        contacts["job_contacts"].append({"name": p[0].strip(), "company": p[1].strip(), "role": p[2].strip(), "user_id": "", "industry": p[3].strip()})
        save_contacts(contacts); return "reply", "Added. They must: /register job " + p[0].strip()
    if tl.startswith("/remove counselor "):
        n = text[18:].strip(); b = len(contacts["counselors"])
        contacts["counselors"] = [c for c in contacts["counselors"] if c["name"].lower() != n.lower()]
        save_contacts(contacts); return "reply", ("Removed." if len(contacts["counselors"]) < b else "Not found.")
    if tl.startswith("/remove tutor "):
        n = text[14:].strip(); b = len(contacts["tutors"])
        contacts["tutors"] = [t for t in contacts["tutors"] if t["name"].lower() != n.lower()]
        save_contacts(contacts); return "reply", ("Removed." if len(contacts["tutors"]) < b else "Not found.")
    if tl.startswith("/remove job "):
        n = text[12:].strip(); b = len(contacts["job_contacts"])
        contacts["job_contacts"] = [j for j in contacts["job_contacts"] if j["name"].lower() != n.lower()]
        save_contacts(contacts); return "reply", ("Removed." if len(contacts["job_contacts"]) < b else "Not found.")
    if tl.startswith("/set scholarship form "):
        contacts["scholarship"]["google_form_url"] = text[22:].strip(); save_contacts(contacts); return "reply", "Updated."
    if tl.startswith("/set scholarship doc "):
        contacts["scholarship"]["google_doc_url"] = text[21:].strip(); save_contacts(contacts); return "reply", "Updated."
    return "reply", "Unknown. /admin for help."

def do_register(uid, text, contacts):
    tl = text.lower().strip()
    if tl.startswith("/register counselor "):
        n = text[20:].strip()
        for c in contacts["counselors"]:
            if c["name"].lower() == n.lower(): c["user_id"] = uid; save_contacts(contacts); return "Registered as counselor: " + n
        return "Not found: " + n
    if tl.startswith("/register tutor "):
        n = text[16:].strip()
        for t in contacts["tutors"]:
            if t["name"].lower() == n.lower(): t["user_id"] = uid; save_contacts(contacts); return "Registered as tutor: " + n
        return "Not found: " + n
    if tl.startswith("/register job "):
        n = text[14:].strip()
        for j in contacts["job_contacts"]:
            if j["name"].lower() == n.lower(): j["user_id"] = uid; save_contacts(contacts); return "Registered as job contact: " + n
        return "Not found: " + n
    if tl == "/register scholarship":
        contacts["scholarship"]["contact_user_id"] = uid; save_contacts(contacts); return "Registered as scholarship contact!"
    return "/register counselor/tutor/job YourName"


# ═══════════════════════════════════════════════════════════════
# MAIN HANDLER
# ═══════════════════════════════════════════════════════════════

@app.route("/callback", methods=["POST"])
def callback():
    sig = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try: webhook_handler.handle(body, sig)
    except InvalidSignatureError: abort(400)
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
        action, result = handle_cmd(uid, text)
        if action == "chats":
            hs = sessions.get(uid)
            if hs and hs.get("type") == "helper":
                reply(event.reply_token, ui_inbox(hs))
            else:
                reply(event.reply_token, T("No active conversations."))
        else:
            reply(event.reply_token, T(result))
        return

    us = sessions.get(uid)

    # 2. Student in conversation
    if us and us.get("type") == "student":
        if tl == "exit":
            disconnect(uid, sessions)
            reply(event.reply_token, ui_ended(us["connected_name"]))
            return
        hid = us["connected_to"]
        sname = get_name(uid)
        cat = us.get("category", "tutor")
        try:
            hs = sessions.get(hid)
            if hs and hs.get("type") == "helper":
                hs["replying_to"] = uid
                if uid in hs["conversations"]:
                    hs["conversations"][uid]["last_message"] = text[:50]
                save_sessions(sessions)
            push(hid, ui_student_message(sname, text, cat))
            reply(event.reply_token, ui_sent())
        except Exception as e:
            reply(event.reply_token, T("Delivery failed: " + str(e)[:60]))
        return

    # 3. Helper in conversation
    if us and us.get("type") == "helper":
        convos = us.get("conversations", {})

        if tl.startswith("exit "):
            tn = text[5:].strip()
            for sid, info in convos.items():
                if info["name"].lower() == tn.lower():
                    try: push(sid, ui_ended(get_name(uid)))
                    except: pass
                    disconnect(sid, sessions)
                    reply(event.reply_token, ui_ended(tn))
                    return
            reply(event.reply_token, T("No chat with '" + tn + "'. /chats to see all."))
            return

        if tl == "exit":
            if len(convos) == 1:
                sid = list(convos.keys())[0]; sn = convos[sid]["name"]
                try: push(sid, ui_ended(get_name(uid)))
                except: pass
                disconnect(sid, sessions)
                reply(event.reply_token, ui_ended(sn))
                return
            reply(event.reply_token, T("Multiple chats open. Use: exit Name"))
            return

        # @Name message
        if text.startswith("@"):
            sp = text.find(" ", 1)
            if sp > 0:
                tn = text[1:sp].strip(); msg = text[sp+1:].strip()
                for sid, info in convos.items():
                    if info["name"].lower() == tn.lower() and msg:
                        hname = get_name(uid)
                        try:
                            push(sid, ui_helper_message(hname, msg))
                            us["replying_to"] = sid; save_sessions(sessions)
                            reply(event.reply_token, ui_sent())
                        except Exception as e:
                            reply(event.reply_token, T("Error: " + str(e)[:60]))
                        return
                reply(event.reply_token, T("No chat with that name. /chats"))
                return

        if tl in ["hi", "hello", "menu", "help", "hey", "inbox"]:
            reply(event.reply_token, ui_inbox(us))
            return

        # Default: send to current replying_to
        rt = us.get("replying_to")
        if rt and rt in convos:
            hname = get_name(uid)
            try:
                push(rt, ui_helper_message(hname, text))
                reply(event.reply_token, ui_sent())
            except Exception as e:
                reply(event.reply_token, T("Error: " + str(e)[:60]))
            return
        reply(event.reply_token, [T("Who should I send this to?"), ui_inbox(us)])
        return

    # 4. Picking
    if uid in pending:
        cat = pending[uid]["category"]
        avail = get_available(cat, contacts)
        if tl == "exit":
            del pending[uid]; save_pending(pending)
            reply(event.reply_token, ui_main_menu())
            return
        try:
            idx = int(text) - 1
            if 0 <= idx < len(avail):
                p = avail[idx]; del pending[uid]; save_pending(pending)
                connect(uid, p["user_id"], p["name"], cat, sessions)
                reply(event.reply_token, T("You are being connected to " + p["name"] + "..."))
                return
            reply(event.reply_token, T("Pick a valid number."))
            return
        except ValueError:
            reply(event.reply_token, T("Reply with a number or 'exit'."))
            return

    # 5. Menu
    if tl in ["hi", "hello", "menu", "start", "help", "hey", "back"]:
        reply(event.reply_token, ui_main_menu())
        return

    # 6. Options
    def try_connect(cat):
        avail = get_available(cat, contacts)
        if not avail:
            reply(event.reply_token, T("No one available yet. Helpers need to register.\nType 'hi' for menu."))
            return
        if len(avail) == 1:
            reply(event.reply_token, T("You are being connected to " + avail[0]["name"] + "..."))
            connect(uid, avail[0]["user_id"], avail[0]["name"], cat, sessions)
            return
        p = ui_picker(cat, contacts)
        if p: pending[uid] = {"category": cat}; save_pending(pending); reply(event.reply_token, p)

    if text in ["1"] or "counselor" in tl or "admission" in tl: try_connect("counselor"); return
    if text in ["2"] or "tutor" in tl or "education" in tl or "test" in tl or "study" in tl: try_connect("tutor"); return
    if text in ["3"] or "scholarship" in tl: reply(event.reply_token, ui_scholarship(contacts)); return
    if tl == "connect":
        si = contacts.get("scholarship", {})
        sid, sn = si.get("contact_user_id", ""), si.get("contact_name", "")
        if sid:
            reply(event.reply_token, T("You are being connected to " + sn + "..."))
            connect(uid, sid, sn, "scholarship", sessions)
        else: reply(event.reply_token, T("Not available yet. Please fill in the form."))
        return
    if text in ["4"] or "job" in tl or "work" in tl or "career" in tl: try_connect("job"); return

    reply(event.reply_token, [T("Welcome!"), ui_main_menu()])

@app.route("/", methods=["GET"])
def health(): return "Running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
