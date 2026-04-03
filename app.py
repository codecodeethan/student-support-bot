"""
LINE Chatbot — Student Support Hub v7
SIMPLE VERSION:
- Students connect, type messages freely
- Helpers DON'T get spammed with every message
- Helpers type 'inbox' to see list of students + unread count
- Helpers type a number to open that student's full chat history
- Helpers reply from there
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

def _load(p, d):
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f: return json.load(f)
    return d
def _save(p, d):
    with open(p, "w", encoding="utf-8") as f: json.dump(d, f, indent=2, ensure_ascii=False)

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
if not os.path.exists(CONTACTS_FILE): save_contacts(DEFAULT_CONTACTS)

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

# Colors
BLUE = "#0066FF"; GREEN = "#00C853"; RED = "#FF3D00"; ORANGE = "#FF9100"
DARK = "#1A1A2E"; GRAY = "#78909C"; LIGHT = "#F5F7FA"; WHITE = "#FFFFFF"
CAT_COLOR = {"counselor": BLUE, "tutor": GREEN, "job": ORANGE, "scholarship": RED}
CAT_LABEL = {"counselor": "Counseling", "tutor": "Education", "job": "Job Search", "scholarship": "Scholarship"}

"""
SESSION STRUCTURE:

sessions = {
    "student_id": {
        "type": "student",
        "helper_id": "xxx",
        "helper_name": "Ethan",
        "category": "tutor",
        "messages": [
            {"from": "student", "name": "Somchai", "text": "Hello", "time": 123456},
            {"from": "helper", "name": "Ethan", "text": "Hi!", "time": 123457},
        ],
        "unread": 0
    },
    "helper_id": {
        "type": "helper",
        "students": {
            "student_id": {"name": "Somchai", "category": "tutor", "unread": 2},
        },
        "viewing": null  // which student's chat they have open
    }
}
"""


# ═══════════════════════════════════════════════════════════════
# STUDENT UI
# ═══════════════════════════════════════════════════════════════

def ui_menu():
    return F("Support Hub", {
        "type": "bubble", "size": "mega",
        "header": {
            "type": "box", "layout": "vertical", "backgroundColor": DARK, "paddingAll": "22px",
            "contents": [
                {"type": "text", "text": "STUDENT", "size": "xxs", "color": "#FFFFFF60", "weight": "bold"},
                {"type": "text", "text": "Support Hub", "size": "xxl", "color": WHITE, "weight": "bold", "margin": "xs"},
                {"type": "text", "text": "Pick an option to get connected", "size": "xs", "color": "#FFFFFF80", "margin": "md"},
            ],
        },
        "body": {
            "type": "box", "layout": "vertical", "spacing": "md", "paddingAll": "18px",
            "contents": [
                _opt("1", "Counselor", "Admissions & academic help", BLUE),
                _opt("2", "Education", "Tutoring & test support", GREEN),
                _opt("3", "Scholarships", "Financial aid & forms", RED),
                _opt("4", "Job Search", "Career & job contacts", ORANGE),
            ],
        },
    })

def _opt(n, title, desc, color):
    return {
        "type": "box", "layout": "horizontal", "spacing": "lg",
        "cornerRadius": "12px", "paddingAll": "14px",
        "borderWidth": "1px", "borderColor": "#E8E8E8",
        "contents": [
            {"type": "box", "layout": "vertical", "width": "40px", "height": "40px",
             "backgroundColor": color, "cornerRadius": "20px",
             "justifyContent": "center", "alignItems": "center",
             "contents": [{"type": "text", "text": n, "color": WHITE, "weight": "bold", "size": "md", "align": "center"}]},
            {"type": "box", "layout": "vertical", "flex": 1,
             "contents": [
                 {"type": "text", "text": title, "weight": "bold", "size": "md", "color": "#1A1A1A"},
                 {"type": "text", "text": desc, "size": "xs", "color": GRAY, "margin": "xs"},
             ]},
        ],
    }

def ui_scholarship(contacts):
    info = contacts.get("scholarship", {})
    msgs = [F("Scholarships", {
        "type": "bubble", "size": "mega",
        "header": {"type": "box", "layout": "vertical", "paddingAll": "20px", "backgroundColor": RED,
                   "contents": [
                       {"type": "text", "text": "SCHOLARSHIPS", "size": "xxs", "color": "#FFFFFF80", "weight": "bold"},
                       {"type": "text", "text": "Financial Support", "size": "xl", "color": WHITE, "weight": "bold", "margin": "xs"},
                   ]},
        "body": {"type": "box", "layout": "vertical", "paddingAll": "18px",
                 "contents": [{"type": "text", "text": info.get("description", ""), "size": "sm", "color": GRAY, "wrap": True}]},
        "footer": {"type": "box", "layout": "vertical", "spacing": "sm", "paddingAll": "14px",
                   "contents": [
                       {"type": "button", "action": {"type": "uri", "label": "Fill Application Form", "uri": info.get("google_form_url", "https://docs.google.com/forms")}, "style": "primary", "color": RED, "height": "sm"},
                       {"type": "button", "action": {"type": "uri", "label": "View Details", "uri": info.get("google_doc_url", "https://docs.google.com/document")}, "style": "secondary", "height": "sm"},
                   ]},
    })]
    if info.get("contact_user_id"):
        msgs.append(T("Want to talk to someone about scholarships? Type 'connect'"))
    return msgs

def ui_picker(cat, contacts):
    avail = get_available(cat, contacts)
    if len(avail) <= 1: return None
    color = CAT_COLOR.get(cat, BLUE)
    label = {"counselor": "Counselors", "tutor": "Tutors", "job": "Job Contacts"}.get(cat, "")
    rows = []
    for i, p in enumerate(avail, 1):
        sub = p.get("role", "")
        if cat == "tutor" and p.get("subjects"): sub = ", ".join(p["subjects"])
        if cat == "job" and p.get("company"): sub = p["company"]
        rows.append({
            "type": "box", "layout": "horizontal", "spacing": "md",
            "cornerRadius": "10px", "paddingAll": "12px", "borderWidth": "1px", "borderColor": "#E8E8E8",
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
        "header": {"type": "box", "layout": "vertical", "paddingAll": "16px", "backgroundColor": color + "15",
                   "contents": [
                       {"type": "text", "text": "Available " + label, "size": "md", "weight": "bold", "color": color},
                       {"type": "text", "text": "Reply with a number", "size": "xs", "color": GRAY, "margin": "sm"},
                   ]},
        "body": {"type": "box", "layout": "vertical", "spacing": "sm", "paddingAll": "14px", "contents": rows},
    })


# ═══════════════════════════════════════════════════════════════
# HELPER UI — INBOX + CHAT HISTORY
# ═══════════════════════════════════════════════════════════════

def ui_inbox(helper_session):
    """Shows list of students with unread counts. Like Instagram DM list."""
    students = helper_session.get("students", {})
    if not students:
        return F("Inbox", {
            "type": "bubble", "size": "mega",
            "header": {"type": "box", "layout": "vertical", "paddingAll": "16px", "backgroundColor": DARK,
                       "contents": [{"type": "text", "text": "Inbox", "color": WHITE, "weight": "bold", "size": "lg"}]},
            "body": {"type": "box", "layout": "vertical", "paddingAll": "30px",
                     "contents": [{"type": "text", "text": "No conversations yet", "color": GRAY, "align": "center"}]},
        })

    total_unread = sum(s.get("unread", 0) for s in students.values())
    rows = []
    for i, (sid, info) in enumerate(students.items(), 1):
        unread = info.get("unread", 0)
        color = CAT_COLOR.get(info.get("category", "tutor"), GREEN)
        cat_short = {"counselor": "CNS", "tutor": "EDU", "job": "JOB", "scholarship": "SCH"}.get(info.get("category", ""), "")

        row_contents = [
            # Number
            {"type": "text", "text": str(i), "size": "sm", "color": GRAY, "weight": "bold", "gravity": "center", "flex": 0},
            # Avatar
            {"type": "box", "layout": "vertical", "width": "40px", "height": "40px",
             "backgroundColor": color, "cornerRadius": "20px",
             "justifyContent": "center", "alignItems": "center", "flex": 0,
             "contents": [{"type": "text", "text": info["name"][0].upper(), "color": WHITE, "weight": "bold", "size": "md", "align": "center"}]},
            # Name + category
            {"type": "box", "layout": "vertical", "flex": 1,
             "contents": [
                 {"type": "text", "text": info["name"], "weight": "bold", "size": "sm", "color": "#1A1A1A"},
                 {"type": "text", "text": cat_short, "size": "xxs", "color": color, "weight": "bold", "margin": "xs"},
             ]},
        ]

        # Unread badge
        if unread > 0:
            row_contents.append(
                {"type": "box", "layout": "vertical", "width": "24px", "height": "24px",
                 "backgroundColor": RED, "cornerRadius": "12px",
                 "justifyContent": "center", "alignItems": "center", "flex": 0,
                 "contents": [{"type": "text", "text": str(unread), "color": WHITE, "size": "xs", "weight": "bold", "align": "center"}]}
            )

        rows.append({
            "type": "box", "layout": "horizontal", "spacing": "md",
            "paddingAll": "12px", "cornerRadius": "10px",
            "borderWidth": "1px", "borderColor": RED if unread > 0 else "#E8E8E8",
            "backgroundColor": "#FFF5F5" if unread > 0 else WHITE,
            "contents": row_contents,
        })

    header_contents = [
        {"type": "text", "text": "Inbox", "color": WHITE, "weight": "bold", "size": "lg", "flex": 1},
    ]
    if total_unread > 0:
        header_contents.append(
            {"type": "box", "layout": "vertical", "backgroundColor": RED, "cornerRadius": "12px",
             "paddingStart": "8px", "paddingEnd": "8px", "paddingTop": "4px", "paddingBottom": "4px", "flex": 0,
             "contents": [{"type": "text", "text": str(total_unread) + " new", "color": WHITE, "size": "xxs", "weight": "bold", "align": "center"}]}
        )

    return F("Inbox", {
        "type": "bubble", "size": "mega",
        "header": {"type": "box", "layout": "horizontal", "paddingAll": "16px", "backgroundColor": DARK, "contents": header_contents},
        "body": {"type": "box", "layout": "vertical", "spacing": "sm", "paddingAll": "12px", "contents": rows},
        "footer": {"type": "box", "layout": "vertical", "paddingAll": "10px", "backgroundColor": LIGHT,
                   "contents": [
                       {"type": "text", "text": "Reply with a number to open chat", "size": "xxs", "color": GRAY, "align": "center"},
                       {"type": "text", "text": "exit Name = end conversation", "size": "xxs", "color": GRAY, "align": "center", "margin": "xs"},
                   ]},
    })


def ui_chat_history(student_name, messages, category):
    """Horizontal swipeable carousel — each bubble = one message. Like swiping through DMs."""
    color = CAT_COLOR.get(category, GREEN)
    # LINE carousel max 12 bubbles: 1 header + 10 messages + 1 footer
    recent = messages[-10:] if len(messages) > 10 else messages

    bubbles = []

    # First bubble: header with student info
    bubbles.append({
        "type": "bubble", "size": "kilo",
        "body": {
            "type": "box", "layout": "vertical", "paddingAll": "20px", "spacing": "md",
            "backgroundColor": DARK, "alignItems": "center", "justifyContent": "center",
            "contents": [
                {"type": "box", "layout": "vertical", "width": "48px", "height": "48px",
                 "backgroundColor": color, "cornerRadius": "24px",
                 "justifyContent": "center", "alignItems": "center",
                 "contents": [{"type": "text", "text": student_name[0].upper(), "color": WHITE, "weight": "bold", "size": "xl", "align": "center"}]},
                {"type": "text", "text": student_name, "color": WHITE, "weight": "bold", "size": "lg", "align": "center"},
                {"type": "text", "text": str(len(messages)) + " messages", "color": "#FFFFFF80", "size": "xxs", "align": "center"},
                {"type": "text", "text": "Swipe to read  >>", "color": "#FFFFFF60", "size": "xxs", "align": "center", "margin": "lg"},
            ],
        },
    })

    # Each message = one bubble
    for m in recent:
        is_student = m["from"] == "student"
        name = m.get("name", "?")
        bg = LIGHT if is_student else "#E3F2FD"
        dot_color = color if is_student else BLUE
        label = "Student" if is_student else "You"

        bubbles.append({
            "type": "bubble", "size": "kilo",
            "body": {
                "type": "box", "layout": "vertical", "paddingAll": "16px", "spacing": "sm",
                "contents": [
                    # Who sent it
                    {"type": "box", "layout": "horizontal", "spacing": "sm",
                     "contents": [
                         {"type": "box", "layout": "vertical", "width": "24px", "height": "24px",
                          "backgroundColor": dot_color, "cornerRadius": "12px",
                          "justifyContent": "center", "alignItems": "center",
                          "contents": [{"type": "text", "text": name[0].upper(), "color": WHITE, "weight": "bold", "size": "xxs", "align": "center"}]},
                         {"type": "text", "text": name, "weight": "bold", "size": "xs", "color": "#1A1A1A", "gravity": "center"},
                         {"type": "text", "text": label, "size": "xxs", "color": GRAY, "gravity": "center", "align": "end", "flex": 1},
                     ]},
                    # Message
                    {"type": "box", "layout": "vertical",
                     "backgroundColor": bg, "cornerRadius": "14px", "paddingAll": "12px", "margin": "sm",
                     "contents": [{"type": "text", "text": m["text"], "size": "sm", "color": "#1A1A1A", "wrap": True}]},
                ],
            },
        })

    # Last bubble: reply instruction
    bubbles.append({
        "type": "bubble", "size": "kilo",
        "body": {
            "type": "box", "layout": "vertical", "paddingAll": "20px", "spacing": "md",
            "backgroundColor": LIGHT, "alignItems": "center", "justifyContent": "center",
            "contents": [
                {"type": "text", "text": "Replying to", "size": "xs", "color": GRAY, "align": "center"},
                {"type": "text", "text": student_name, "size": "lg", "weight": "bold", "color": "#1A1A1A", "align": "center"},
                {"type": "separator", "color": "#E0E0E0", "margin": "md"},
                {"type": "text", "text": "Type your message to reply", "size": "xs", "color": GRAY, "align": "center", "margin": "md"},
                {"type": "text", "text": "'inbox' = back", "size": "xxs", "color": "#B0B0B0", "align": "center", "margin": "sm"},
            ],
        },
    })

    return F("Chat with " + student_name, {"type": "carousel", "contents": bubbles})


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
    sessions[student_id] = {
        "type": "student", "helper_id": helper_id, "helper_name": helper_name,
        "category": cat, "messages": [], "unread": 0,
    }
    if helper_id not in sessions or sessions[helper_id].get("type") != "helper":
        sessions[helper_id] = {"type": "helper", "students": {}, "viewing": None}

    # Check if this student is already in helper's list (returning student)
    is_new = student_id not in sessions[helper_id]["students"]

    sessions[helper_id]["students"][student_id] = {"name": sname, "category": cat, "unread": 0}
    save_sessions(sessions)

    # Notify student
    color = CAT_COLOR.get(cat, GREEN)
    label = CAT_LABEL.get(cat, "Support")
    push(student_id, F("Connected", {
        "type": "bubble", "size": "mega",
        "body": {
            "type": "box", "layout": "vertical", "paddingAll": "24px", "spacing": "lg", "alignItems": "center",
            "contents": [
                {"type": "box", "layout": "vertical", "width": "56px", "height": "56px",
                 "backgroundColor": color, "cornerRadius": "28px",
                 "justifyContent": "center", "alignItems": "center",
                 "contents": [{"type": "text", "text": helper_name[0].upper(), "color": WHITE, "weight": "bold", "size": "xxl", "align": "center"}]},
                {"type": "text", "text": "Connected to " + helper_name, "size": "lg", "weight": "bold", "color": "#1A1A1A", "align": "center"},
                {"type": "box", "layout": "horizontal", "backgroundColor": color + "15", "cornerRadius": "20px",
                 "paddingStart": "14px", "paddingEnd": "14px", "paddingTop": "6px", "paddingBottom": "6px",
                 "contents": [{"type": "text", "text": label, "size": "xs", "color": color, "weight": "bold"}]},
                {"type": "separator", "color": "#E8E8E8"},
                {"type": "text", "text": "Type your message and it will be delivered. They will check and respond.", "size": "sm", "color": GRAY, "wrap": True, "align": "center"},
            ],
        },
        "footer": {"type": "box", "layout": "vertical", "paddingAll": "12px", "backgroundColor": LIGHT,
                   "contents": [{"type": "text", "text": "Type 'exit' to end conversation", "size": "xxs", "color": GRAY, "align": "center"}]},
    }))

    # Only notify helper if this is a NEW student
    if is_new:
        push(helper_id, T("New student connected: " + sname + " (" + label + "). Check your inbox when ready."))


def disconnect(student_id, sessions):
    s = sessions.get(student_id)
    if not s or s.get("type") != "student": return
    hid = s["helper_id"]
    sname = "Student"
    hs = sessions.get(hid)
    if hs and hs.get("type") == "helper":
        info = hs["students"].get(student_id, {})
        sname = info.get("name", "Student")
        hs["students"].pop(student_id, None)
        if hs.get("viewing") == student_id: hs["viewing"] = None
        if not hs["students"]: sessions.pop(hid, None)
    sessions.pop(student_id, None)
    save_sessions(sessions)
    return sname


# ═══════════════════════════════════════════════════════════════
# ADMIN
# ═══════════════════════════════════════════════════════════════

ADMIN_HELP = """Commands:
/register counselor/tutor/job YourName
/register scholarship
/add counselor Name | Role | email
/add tutor Name | Role | Subjects
/add job Name | Company | Role | Industry
/remove counselor/tutor/job Name
/set scholarship form <url>
/set scholarship doc <url>
/add admin <user_id>
/my id"""

def handle_cmd(uid, text):
    contacts = load_contacts()
    admins = contacts.get("admin_ids", [])
    if not admins: contacts["admin_ids"] = [uid]; save_contacts(contacts); admins = [uid]
    tl = text.lower().strip()
    if tl == "/my id": return "Your ID: " + uid
    if tl.startswith("/register "): return do_reg(uid, text, contacts)
    if uid not in admins: return "No admin access. ID: " + uid
    if tl in ["/admin", "/help"]: return ADMIN_HELP
    if tl == "/list admins": return "Admins:\n" + "\n".join(admins)
    if tl.startswith("/add admin "): 
        nid = text[11:].strip()
        if nid not in admins: contacts["admin_ids"].append(nid); save_contacts(contacts)
        return "Added."
    if tl.startswith("/add counselor "):
        p = text[15:].split("|")
        if len(p) < 3: return "/add counselor Name | Role | Email"
        contacts["counselors"].append({"name": p[0].strip(), "role": p[1].strip(), "email": p[2].strip(), "user_id": ""})
        save_contacts(contacts); return "Added. They must: /register counselor " + p[0].strip()
    if tl.startswith("/add tutor "):
        p = text[11:].split("|")
        if len(p) < 3: return "/add tutor Name | Role | Subjects"
        contacts["tutors"].append({"name": p[0].strip(), "role": p[1].strip(), "user_id": "", "subjects": [s.strip() for s in p[2].split(",")]})
        save_contacts(contacts); return "Added. They must: /register tutor " + p[0].strip()
    if tl.startswith("/add job "):
        p = text[9:].split("|")
        if len(p) < 4: return "/add job Name | Company | Role | Industry"
        contacts["job_contacts"].append({"name": p[0].strip(), "company": p[1].strip(), "role": p[2].strip(), "user_id": "", "industry": p[3].strip()})
        save_contacts(contacts); return "Added. They must: /register job " + p[0].strip()
    if tl.startswith("/remove counselor "):
        n = text[18:].strip(); b = len(contacts["counselors"])
        contacts["counselors"] = [c for c in contacts["counselors"] if c["name"].lower() != n.lower()]
        save_contacts(contacts); return "Removed." if len(contacts["counselors"]) < b else "Not found."
    if tl.startswith("/remove tutor "):
        n = text[14:].strip(); b = len(contacts["tutors"])
        contacts["tutors"] = [t for t in contacts["tutors"] if t["name"].lower() != n.lower()]
        save_contacts(contacts); return "Removed." if len(contacts["tutors"]) < b else "Not found."
    if tl.startswith("/remove job "):
        n = text[12:].strip(); b = len(contacts["job_contacts"])
        contacts["job_contacts"] = [j for j in contacts["job_contacts"] if j["name"].lower() != n.lower()]
        save_contacts(contacts); return "Removed." if len(contacts["job_contacts"]) < b else "Not found."
    if tl.startswith("/set scholarship form "):
        contacts["scholarship"]["google_form_url"] = text[22:].strip(); save_contacts(contacts); return "Updated."
    if tl.startswith("/set scholarship doc "):
        contacts["scholarship"]["google_doc_url"] = text[21:].strip(); save_contacts(contacts); return "Updated."
    return "Unknown. /admin for help."

def do_reg(uid, text, contacts):
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
        reply(event.reply_token, T(handle_cmd(uid, text)))
        return

    us = sessions.get(uid)

    # ════════════════════════════════════════
    # STUDENT FLOW
    # ════════════════════════════════════════
    if us and us.get("type") == "student":
        if tl == "exit":
            hname = us["helper_name"]
            sname = disconnect(uid, sessions)
            reply(event.reply_token, F("Ended", {
                "type": "bubble", "size": "kilo",
                "body": {"type": "box", "layout": "vertical", "paddingAll": "16px", "backgroundColor": LIGHT, "cornerRadius": "12px",
                         "contents": [
                             {"type": "text", "text": "Chat with " + hname + " ended", "size": "sm", "color": GRAY, "align": "center"},
                             {"type": "text", "text": "Type 'hi' to start over", "size": "xxs", "color": "#B0B0B0", "align": "center", "margin": "sm"},
                         ]},
            }))
            return

        # Store message silently — no notification to helper
        sname = get_name(uid)
        us["messages"].append({"from": "student", "name": sname, "text": text, "time": int(time.time())})

        # Increment unread on helper side
        hid = us["helper_id"]
        hs = sessions.get(hid)
        if hs and hs.get("type") == "helper" and uid in hs["students"]:
            hs["students"][uid]["unread"] = hs["students"][uid].get("unread", 0) + 1

        save_sessions(sessions)

        reply(event.reply_token, F("Delivered", {
            "type": "bubble", "size": "kilo",
            "body": {"type": "box", "layout": "horizontal", "paddingAll": "10px",
                     "contents": [{"type": "text", "text": "Message delivered", "size": "xxs", "color": GREEN, "align": "end", "flex": 1}]},
        }))
        return

    # ════════════════════════════════════════
    # HELPER FLOW
    # ════════════════════════════════════════
    if us and us.get("type") == "helper":
        students = us.get("students", {})

        # "inbox" — show inbox
        if tl in ["inbox", "hi", "hello", "menu", "help", "hey"]:
            us["viewing"] = None
            save_sessions(sessions)
            reply(event.reply_token, ui_inbox(us))
            return

        # "exit Name" — disconnect student
        if tl.startswith("exit "):
            tn = text[5:].strip()
            for sid, info in students.items():
                if info["name"].lower() == tn.lower():
                    hname = get_name(uid)
                    ss = sessions.get(sid)
                    if ss:
                        try: push(sid, T("Chat with " + hname + " has ended. Type 'hi' to start over."))
                        except: pass
                    disconnect(sid, sessions)
                    sessions = load_sessions()
                    reply(event.reply_token, T("Ended chat with " + tn + "."))
                    return
            reply(event.reply_token, T("No chat with '" + tn + "'. Type 'inbox'."))
            return

        # Number — open that student's chat
        if not us.get("viewing"):
            try:
                idx = int(text) - 1
                student_list = list(students.items())
                if 0 <= idx < len(student_list):
                    sid, info = student_list[idx]
                    # Mark as read
                    info["unread"] = 0
                    us["viewing"] = sid
                    save_sessions(sessions)

                    # Get messages from student session
                    ss = sessions.get(sid, {})
                    msgs = ss.get("messages", [])
                    cat = info.get("category", "tutor")

                    reply(event.reply_token, ui_chat_history(info["name"], msgs, cat))
                    return
                reply(event.reply_token, T("Invalid number. Type 'inbox'."))
                return
            except ValueError:
                pass

        # If viewing a student — send reply to that student
        viewing = us.get("viewing")
        if viewing and viewing in students:
            sinfo = students[viewing]
            ss = sessions.get(viewing)
            if ss and ss.get("type") == "student":
                hname = get_name(uid)
                # Store message in student's session
                ss["messages"].append({"from": "helper", "name": hname, "text": text, "time": int(time.time())})
                ss["unread"] = ss.get("unread", 0) + 1
                save_sessions(sessions)

                # Deliver to student as a simple text
                try:
                    push(viewing, T(hname + ": " + text))
                except: pass

                reply(event.reply_token, F("Sent", {
                    "type": "bubble", "size": "kilo",
                    "body": {"type": "box", "layout": "horizontal", "paddingAll": "10px",
                             "contents": [{"type": "text", "text": "Sent to " + sinfo["name"], "size": "xxs", "color": GREEN, "align": "end", "flex": 1}]},
                }))
                return
            else:
                us["viewing"] = None; save_sessions(sessions)
                reply(event.reply_token, T("That student disconnected. Type 'inbox'."))
                return

        # Fallback
        reply(event.reply_token, [T("Type 'inbox' to see your conversations."), ui_inbox(us)])
        return

    # ════════════════════════════════════════
    # PICKING FROM LIST
    # ════════════════════════════════════════
    if uid in pending:
        cat = pending[uid]["category"]
        avail = get_available(cat, contacts)
        if tl == "exit":
            del pending[uid]; save_pending(pending)
            reply(event.reply_token, ui_menu())
            return
        try:
            idx = int(text) - 1
            if 0 <= idx < len(avail):
                p = avail[idx]; del pending[uid]; save_pending(pending)
                reply(event.reply_token, T("Connecting you to " + p["name"] + "..."))
                connect(uid, p["user_id"], p["name"], cat, sessions)
                return
            reply(event.reply_token, T("Pick a valid number."))
            return
        except ValueError:
            reply(event.reply_token, T("Reply with a number or 'exit'."))
            return

    # ════════════════════════════════════════
    # MAIN MENU
    # ════════════════════════════════════════
    if tl in ["hi", "hello", "menu", "start", "help", "hey", "back"]:
        reply(event.reply_token, ui_menu())
        return

    def try_connect(cat):
        avail = get_available(cat, contacts)
        if not avail:
            reply(event.reply_token, T("No one available yet. Type 'hi' for menu."))
            return
        if len(avail) == 1:
            reply(event.reply_token, T("Connecting you to " + avail[0]["name"] + "..."))
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
        if sid: reply(event.reply_token, T("Connecting you to " + sn + "...")); connect(uid, sid, sn, "scholarship", sessions)
        else: reply(event.reply_token, T("Not available yet. Fill in the form."))
        return
    if text in ["4"] or "job" in tl or "work" in tl or "career" in tl: try_connect("job"); return

    reply(event.reply_token, [T("Welcome!"), ui_menu()])

@app.route("/", methods=["GET"])
def health(): return "Running!"
if __name__ == "__main__": app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
