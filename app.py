"""
LINE Chatbot — Student Support Hub v5
Beautiful Flex Message UI + multi-conversation relay
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


def _load(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def _save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_contacts(): return _load(CONTACTS_FILE, DEFAULT_CONTACTS)
def save_contacts(data): _save(CONTACTS_FILE, data)
def load_sessions(): return _load(SESSIONS_FILE, {})
def save_sessions(data): _save(SESSIONS_FILE, data)
def load_pending(): return _load(PENDING_FILE, {})
def save_pending(data): _save(PENDING_FILE, data)

DEFAULT_CONTACTS = {
    "counselors": [{"name": "Khun Somporn", "role": "Admissions & Academic Guidance", "user_id": "", "email": "somporn@school.ac.th"}],
    "tutors": [{"name": "Ethan", "role": "Team Lead - General Support", "user_id": "", "subjects": ["Math", "Science", "English"]}],
    "scholarship": {
        "contact_name": "Ethan", "contact_user_id": "",
        "google_form_url": "https://docs.google.com/forms/d/e/YOUR_FORM_ID/viewform",
        "google_doc_url": "https://docs.google.com/document/d/YOUR_DOC_ID/edit",
        "description": "We offer guidance on scholarships for students at risk of dropping out. Fill in the form and we will match you with opportunities.",
    },
    "job_contacts": [{"name": "Job Fair Contact", "company": "Company Name", "role": "HR / Recruiter", "user_id": "", "industry": "Technology"}],
    "admin_ids": [],
}
if not os.path.exists(CONTACTS_FILE):
    save_contacts(DEFAULT_CONTACTS)


# ─── Messaging helpers ──────────────────────────────────────────

def get_api():
    return MessagingApi(ApiClient(configuration))

def reply(token, messages):
    if not isinstance(messages, list): messages = [messages]
    get_api().reply_message(ReplyMessageRequest(reply_token=token, messages=messages))

def push(user_id, messages):
    if not isinstance(messages, list): messages = [messages]
    get_api().push_message(PushMessageRequest(to=user_id, messages=messages))

def T(t): return TextMessage(text=t)

def F(alt, d): return FlexMessage(alt_text=alt, contents=FlexContainer.from_dict(d))

def get_display_name(user_id):
    try: return get_api().get_profile(user_id).display_name
    except: return "Someone"


# ─── Beautiful Flex Message Builders ─────────────────────────────

# Color palette
C = {
    "blue": "#0066FF",
    "blue_light": "#E8F0FE",
    "green": "#00C853",
    "green_light": "#E8F5E9",
    "red": "#FF3D00",
    "red_light": "#FFEBEE",
    "orange": "#FF9100",
    "orange_light": "#FFF3E0",
    "gray": "#78909C",
    "gray_light": "#F5F5F5",
    "dark": "#1A1A2E",
    "white": "#FFFFFF",
    "text": "#263238",
    "text_sub": "#78909C",
}


def build_main_menu():
    return F("Student Support Hub", {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": C["dark"],
            "paddingAll": "24px",
            "contents": [
                {"type": "text", "text": "STUDENT", "size": "sm", "color": "#FFFFFF80", "weight": "bold", "letterSpacing": "3px"},
                {"type": "text", "text": "Support Hub", "size": "xxl", "color": C["white"], "weight": "bold", "margin": "xs"},
                {"type": "text", "text": "Tap an option below to get connected", "size": "xs", "color": "#FFFFFF90", "margin": "lg"},
            ],
        },
        "body": {
            "type": "box", "layout": "vertical", "spacing": "lg", "paddingAll": "20px",
            "contents": [
                _menu_card("1", "Counselor", "Admissions, academic guidance", C["blue"], C["blue_light"]),
                _menu_card("2", "Education Help", "Tutoring, test prep, study support", C["green"], C["green_light"]),
                _menu_card("3", "Scholarships", "Financial aid, application forms", C["red"], C["red_light"]),
                _menu_card("4", "Job Search", "Career contacts from job fairs", C["orange"], C["orange_light"]),
            ],
        },
        "footer": {
            "type": "box", "layout": "vertical", "paddingAll": "16px",
            "contents": [
                {"type": "text", "text": "Reply with 1, 2, 3, or 4", "size": "xs", "color": C["text_sub"], "align": "center"},
            ],
        },
    })


def _menu_card(num, title, desc, color, bg_color):
    return {
        "type": "box", "layout": "horizontal", "spacing": "lg",
        "backgroundColor": bg_color,
        "cornerRadius": "12px",
        "paddingAll": "16px",
        "contents": [
            {
                "type": "box", "layout": "vertical",
                "width": "44px", "height": "44px",
                "backgroundColor": color,
                "cornerRadius": "22px",
                "justifyContent": "center", "alignItems": "center",
                "contents": [{"type": "text", "text": num, "size": "lg", "color": C["white"], "weight": "bold", "align": "center"}],
            },
            {
                "type": "box", "layout": "vertical", "flex": 1,
                "contents": [
                    {"type": "text", "text": title, "size": "md", "weight": "bold", "color": C["text"]},
                    {"type": "text", "text": desc, "size": "xs", "color": C["text_sub"], "margin": "xs", "wrap": True},
                ],
            },
        ],
    }


def build_connecting_card(helper_name, category):
    emoji = {"counselor": "graduation cap", "tutor": "books", "job": "briefcase", "scholarship": "trophy"}.get(category, "")
    label = {"counselor": "Counselor", "tutor": "Education Support", "job": "Job Contact", "scholarship": "Scholarship"}.get(category, category)
    color = {"counselor": C["blue"], "tutor": C["green"], "job": C["orange"], "scholarship": C["red"]}.get(category, C["blue"])
    bg = {"counselor": C["blue_light"], "tutor": C["green_light"], "job": C["orange_light"], "scholarship": C["red_light"]}.get(category, C["blue_light"])

    return F("Connected to " + helper_name, {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box", "layout": "vertical", "paddingAll": "24px", "spacing": "lg",
            "contents": [
                # Status badge
                {
                    "type": "box", "layout": "horizontal", "spacing": "sm",
                    "contents": [
                        {"type": "box", "layout": "vertical", "width": "10px", "height": "10px", "backgroundColor": C["green"], "cornerRadius": "5px", "margin": "sm"},
                        {"type": "text", "text": "CONNECTED", "size": "xxs", "color": C["green"], "weight": "bold"},
                    ],
                },
                # Name + role
                {"type": "text", "text": helper_name, "size": "xl", "weight": "bold", "color": C["text"]},
                {
                    "type": "box", "layout": "horizontal", "spacing": "sm",
                    "backgroundColor": bg, "cornerRadius": "20px",
                    "paddingStart": "12px", "paddingEnd": "12px", "paddingTop": "6px", "paddingBottom": "6px",
                    "width": "180px",
                    "contents": [
                        {"type": "text", "text": label, "size": "xs", "color": color, "weight": "bold"},
                    ],
                },
                {"type": "separator", "color": "#E0E0E0"},
                # Instructions
                {"type": "text", "text": "Type your message below and it will be forwarded directly.", "size": "sm", "color": C["text_sub"], "wrap": True},
                {
                    "type": "box", "layout": "vertical",
                    "backgroundColor": C["gray_light"], "cornerRadius": "8px", "paddingAll": "12px",
                    "contents": [
                        {"type": "text", "text": "Type 'exit' to end this conversation", "size": "xs", "color": C["gray"], "align": "center"},
                    ],
                },
            ],
        },
    })


def build_incoming_card(student_name, category, conv_count):
    label = {"counselor": "Counseling", "tutor": "Education", "job": "Job Search", "scholarship": "Scholarship"}.get(category, category)
    color = {"counselor": C["blue"], "tutor": C["green"], "job": C["orange"], "scholarship": C["red"]}.get(category, C["blue"])

    contents = [
        {
            "type": "box", "layout": "horizontal",
            "contents": [
                {"type": "text", "text": "NEW CHAT", "size": "xxs", "color": C["white"], "weight": "bold"},
            ],
            "backgroundColor": color, "cornerRadius": "4px",
            "paddingStart": "8px", "paddingEnd": "8px", "paddingTop": "4px", "paddingBottom": "4px",
            "width": "80px",
        },
        {"type": "text", "text": student_name, "size": "xl", "weight": "bold", "color": C["text"], "margin": "md"},
        {"type": "text", "text": "Needs help with: " + label, "size": "sm", "color": C["text_sub"], "margin": "xs"},
        {"type": "separator", "color": "#E0E0E0", "margin": "lg"},
        {"type": "text", "text": "Just reply normally to respond.", "size": "sm", "color": C["text_sub"], "margin": "lg", "wrap": True},
    ]

    if conv_count > 1:
        contents.append({
            "type": "box", "layout": "vertical",
            "backgroundColor": C["gray_light"], "cornerRadius": "8px", "paddingAll": "12px", "margin": "lg",
            "contents": [
                {"type": "text", "text": "You have " + str(conv_count) + " active chats", "size": "xs", "color": C["text"], "weight": "bold", "align": "center"},
                {"type": "text", "text": "@Name message  =  reply to specific person", "size": "xxs", "color": C["gray"], "align": "center", "margin": "sm"},
                {"type": "text", "text": "exit Name  =  end a specific chat", "size": "xxs", "color": C["gray"], "align": "center", "margin": "xs"},
                {"type": "text", "text": "/chats  =  see all conversations", "size": "xxs", "color": C["gray"], "align": "center", "margin": "xs"},
            ],
        })

    return F("New chat from " + student_name, {
        "type": "bubble", "size": "mega",
        "body": {"type": "box", "layout": "vertical", "paddingAll": "24px", "spacing": "sm", "contents": contents},
    })


def build_inbox(helper_session):
    convos = helper_session.get("conversations", {})
    replying_to = helper_session.get("replying_to")

    if not convos:
        return F("No active chats", {
            "type": "bubble",
            "body": {"type": "box", "layout": "vertical", "paddingAll": "24px", "contents": [
                {"type": "text", "text": "No active conversations", "size": "md", "color": C["text_sub"], "align": "center"},
            ]},
        })

    chat_rows = []
    for sid, info in convos.items():
        is_current = sid == replying_to
        cat = info.get("category", "?")
        color = {"counselor": C["blue"], "tutor": C["green"], "job": C["orange"], "scholarship": C["red"]}.get(cat, C["blue"])
        label = {"counselor": "Counseling", "tutor": "Education", "job": "Job", "scholarship": "Scholarship"}.get(cat, cat)

        elapsed = int(time.time()) - info.get("started", int(time.time()))
        if elapsed < 60:
            time_str = "Just now"
        elif elapsed < 3600:
            time_str = str(elapsed // 60) + "m ago"
        else:
            time_str = str(elapsed // 3600) + "h ago"

        row = {
            "type": "box", "layout": "horizontal", "spacing": "lg",
            "backgroundColor": C["blue_light"] if is_current else C["white"],
            "cornerRadius": "12px",
            "paddingAll": "14px",
            "borderWidth": "2px" if is_current else "1px",
            "borderColor": C["blue"] if is_current else "#E0E0E0",
            "contents": [
                # Colored dot
                {
                    "type": "box", "layout": "vertical",
                    "width": "40px", "height": "40px",
                    "backgroundColor": color, "cornerRadius": "20px",
                    "justifyContent": "center", "alignItems": "center",
                    "contents": [
                        {"type": "text", "text": info["name"][0].upper(), "size": "md", "color": C["white"], "weight": "bold", "align": "center"},
                    ],
                },
                # Info
                {
                    "type": "box", "layout": "vertical", "flex": 1,
                    "contents": [
                        {
                            "type": "box", "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": info["name"], "size": "sm", "weight": "bold", "color": C["text"], "flex": 1},
                                {"type": "text", "text": time_str, "size": "xxs", "color": C["text_sub"], "align": "end"},
                            ],
                        },
                        {
                            "type": "box", "layout": "horizontal", "spacing": "sm", "margin": "xs",
                            "contents": [
                                {"type": "text", "text": label, "size": "xxs", "color": color, "weight": "bold"},
                                {"type": "text", "text": " << replying" if is_current else "", "size": "xxs", "color": C["blue"]},
                            ],
                        },
                    ],
                },
            ],
        }
        chat_rows.append(row)

    return F("Your conversations", {
        "type": "bubble", "size": "mega",
        "header": {
            "type": "box", "layout": "horizontal",
            "backgroundColor": C["dark"], "paddingAll": "18px",
            "contents": [
                {"type": "text", "text": "Inbox", "size": "lg", "color": C["white"], "weight": "bold", "flex": 1},
                {
                    "type": "box", "layout": "vertical",
                    "backgroundColor": C["blue"], "cornerRadius": "12px",
                    "paddingStart": "10px", "paddingEnd": "10px", "paddingTop": "4px", "paddingBottom": "4px",
                    "contents": [{"type": "text", "text": str(len(convos)), "size": "sm", "color": C["white"], "weight": "bold", "align": "center"}],
                },
            ],
        },
        "body": {
            "type": "box", "layout": "vertical", "spacing": "sm", "paddingAll": "16px",
            "contents": chat_rows,
        },
        "footer": {
            "type": "box", "layout": "vertical", "paddingAll": "12px",
            "backgroundColor": C["gray_light"], "cornerRadius": "0px",
            "contents": [
                {"type": "text", "text": "@Name message = reply to specific person", "size": "xxs", "color": C["gray"], "align": "center"},
                {"type": "text", "text": "exit Name = end chat  |  /chats = refresh", "size": "xxs", "color": C["gray"], "align": "center", "margin": "xs"},
            ],
        },
    })


def build_person_picker_flex(category, contacts):
    available = get_available(category, contacts)
    if len(available) <= 1:
        return None

    color = {"counselor": C["blue"], "tutor": C["green"], "job": C["orange"], "scholarship": C["red"]}.get(category, C["blue"])
    bg = {"counselor": C["blue_light"], "tutor": C["green_light"], "job": C["orange_light"], "scholarship": C["red_light"]}.get(category, C["blue_light"])
    label = {"counselor": "Counselors", "tutor": "Tutors", "job": "Job Contacts", "scholarship": "Scholarship"}.get(category, "")

    rows = []
    for i, p in enumerate(available, 1):
        subtitle = p.get("role", "")
        if category == "tutor" and p.get("subjects"):
            subtitle = ", ".join(p["subjects"])
        elif category == "job" and p.get("company"):
            subtitle = p["company"] + " - " + p.get("role", "")

        rows.append({
            "type": "box", "layout": "horizontal", "spacing": "lg",
            "backgroundColor": C["white"], "cornerRadius": "12px",
            "paddingAll": "14px", "borderWidth": "1px", "borderColor": "#E0E0E0",
            "contents": [
                {
                    "type": "box", "layout": "vertical",
                    "width": "36px", "height": "36px",
                    "backgroundColor": color, "cornerRadius": "18px",
                    "justifyContent": "center", "alignItems": "center",
                    "contents": [{"type": "text", "text": str(i), "size": "md", "color": C["white"], "weight": "bold", "align": "center"}],
                },
                {
                    "type": "box", "layout": "vertical", "flex": 1,
                    "contents": [
                        {"type": "text", "text": p["name"], "size": "sm", "weight": "bold", "color": C["text"]},
                        {"type": "text", "text": subtitle, "size": "xs", "color": C["text_sub"], "margin": "xs", "wrap": True},
                    ],
                },
            ],
        })

    return F("Choose " + label, {
        "type": "bubble", "size": "mega",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": bg, "paddingAll": "18px",
            "contents": [
                {"type": "text", "text": "Available " + label, "size": "lg", "weight": "bold", "color": color},
                {"type": "text", "text": "Reply with a number to connect", "size": "xs", "color": C["text_sub"], "margin": "sm"},
            ],
        },
        "body": {"type": "box", "layout": "vertical", "spacing": "sm", "paddingAll": "16px", "contents": rows},
        "footer": {
            "type": "box", "layout": "vertical", "paddingAll": "12px",
            "contents": [{"type": "text", "text": "Type 'exit' to go back", "size": "xs", "color": C["text_sub"], "align": "center"}],
        },
    })


def build_scholarship_messages(contacts):
    info = contacts.get("scholarship", {})
    flex = F("Scholarship Support", {
        "type": "bubble", "size": "mega",
        "header": {
            "type": "box", "layout": "vertical",
            "backgroundColor": C["red"], "paddingAll": "20px",
            "contents": [
                {"type": "text", "text": "SCHOLARSHIP", "size": "xs", "color": "#FFFFFF80", "weight": "bold", "letterSpacing": "2px"},
                {"type": "text", "text": "Support", "size": "xl", "color": C["white"], "weight": "bold", "margin": "xs"},
            ],
        },
        "body": {
            "type": "box", "layout": "vertical", "paddingAll": "20px", "spacing": "lg",
            "contents": [
                {"type": "text", "text": info.get("description", ""), "size": "sm", "color": C["text_sub"], "wrap": True},
                {"type": "separator", "color": "#E0E0E0"},
                {"type": "text", "text": "Contact: " + info.get("contact_name", "Ethan"), "size": "sm", "color": C["text"]},
            ],
        },
        "footer": {
            "type": "box", "layout": "vertical", "spacing": "sm", "paddingAll": "14px",
            "contents": [
                {"type": "button", "action": {"type": "uri", "label": "Fill Scholarship Form", "uri": info.get("google_form_url", "https://docs.google.com/forms")}, "style": "primary", "color": C["red"], "height": "sm"},
                {"type": "button", "action": {"type": "uri", "label": "View Scholarship Doc", "uri": info.get("google_doc_url", "https://docs.google.com/document")}, "style": "secondary", "height": "sm"},
            ],
        },
    })
    msgs = [flex]
    if info.get("contact_user_id"):
        msgs.append(T("Want to chat directly about scholarships? Type 'connect'"))
    return msgs


def build_sent_card(to_name):
    return F("Sent", {
        "type": "bubble", "size": "kilo",
        "body": {
            "type": "box", "layout": "horizontal", "paddingAll": "12px", "spacing": "sm",
            "backgroundColor": C["green_light"], "cornerRadius": "8px",
            "contents": [
                {"type": "text", "text": "Sent to " + to_name, "size": "xs", "color": C["green"], "weight": "bold", "flex": 1, "gravity": "center"},
            ],
        },
    })


def build_ended_card(name):
    return F("Chat ended", {
        "type": "bubble", "size": "kilo",
        "body": {
            "type": "box", "layout": "vertical", "paddingAll": "16px",
            "backgroundColor": C["gray_light"], "cornerRadius": "8px",
            "contents": [
                {"type": "text", "text": "Conversation with " + name + " ended", "size": "sm", "color": C["text_sub"], "align": "center", "wrap": True},
                {"type": "text", "text": "Type 'hi' for the menu", "size": "xs", "color": C["gray"], "align": "center", "margin": "sm"},
            ],
        },
    })


def build_message_card(sender_name, message_text, color):
    """Incoming message styled as a chat bubble."""
    return F("Message from " + sender_name, {
        "type": "bubble", "size": "mega",
        "body": {
            "type": "box", "layout": "vertical", "paddingAll": "16px", "spacing": "sm",
            "contents": [
                {
                    "type": "box", "layout": "horizontal", "spacing": "sm",
                    "contents": [
                        {
                            "type": "box", "layout": "vertical",
                            "width": "32px", "height": "32px",
                            "backgroundColor": color, "cornerRadius": "16px",
                            "justifyContent": "center", "alignItems": "center",
                            "contents": [{"type": "text", "text": sender_name[0].upper(), "size": "sm", "color": C["white"], "weight": "bold", "align": "center"}],
                        },
                        {"type": "text", "text": sender_name, "size": "sm", "weight": "bold", "color": C["text"], "gravity": "center"},
                    ],
                },
                {
                    "type": "box", "layout": "vertical",
                    "backgroundColor": C["gray_light"], "cornerRadius": "12px",
                    "paddingAll": "14px", "margin": "sm",
                    "contents": [
                        {"type": "text", "text": message_text, "size": "md", "color": C["text"], "wrap": True},
                    ],
                },
            ],
        },
    })


# ─── Connection logic ───────────────────────────────────────────

def get_available(category, contacts):
    if category == "counselor": return [p for p in contacts.get("counselors", []) if p.get("user_id")]
    elif category == "tutor": return [p for p in contacts.get("tutors", []) if p.get("user_id")]
    elif category == "job": return [p for p in contacts.get("job_contacts", []) if p.get("user_id")]
    elif category == "scholarship":
        uid = contacts.get("scholarship", {}).get("contact_user_id", "")
        name = contacts.get("scholarship", {}).get("contact_name", "")
        return [{"name": name, "user_id": uid}] if uid else []
    return []

def connect_users(student_id, helper_id, helper_name, category, sessions):
    student_name = get_display_name(student_id)
    sessions[student_id] = {"type": "student", "connected_to": helper_id, "connected_name": helper_name, "category": category, "started": int(time.time())}
    if helper_id not in sessions:
        sessions[helper_id] = {"type": "helper", "conversations": {}, "replying_to": None}
    elif sessions[helper_id].get("type") != "helper":
        sessions[helper_id] = {"type": "helper", "conversations": {}, "replying_to": None}
    sessions[helper_id]["conversations"][student_id] = {"name": student_name, "category": category, "started": int(time.time())}
    if len(sessions[helper_id]["conversations"]) == 1:
        sessions[helper_id]["replying_to"] = student_id
    else:
        sessions[helper_id]["replying_to"] = student_id
    save_sessions(sessions)

    push(student_id, build_connecting_card(helper_name, category))
    conv_count = len(sessions[helper_id]["conversations"])
    push(helper_id, build_incoming_card(student_name, category, conv_count))

def disconnect_student(student_id, sessions):
    session = sessions.get(student_id)
    if not session or session.get("type") != "student": return
    helper_id = session["connected_to"]
    student_name = get_display_name(student_id)
    sessions.pop(student_id, None)
    hs = sessions.get(helper_id)
    if hs and hs.get("type") == "helper":
        hs["conversations"].pop(student_id, None)
        remaining = hs["conversations"]
        if not remaining:
            sessions.pop(helper_id, None)
            try: push(helper_id, build_ended_card(student_name))
            except: pass
        else:
            if hs.get("replying_to") == student_id:
                next_id = list(remaining.keys())[-1]
                hs["replying_to"] = next_id
            try: push(helper_id, [build_ended_card(student_name), build_inbox(hs)])
            except: pass
    save_sessions(sessions)


# ─── Admin / Register ───────────────────────────────────────────

ADMIN_HELP = """Admin Commands:

/register counselor YourName
/register tutor YourName
/register job YourName
/register scholarship
/add counselor Name | Role | email
/add tutor Name | Role | Subject1, Subject2
/add job Name | Company | Role | Industry
/remove counselor/tutor/job Name
/set scholarship form <url>
/set scholarship doc <url>
/add admin <user_id>
/list admins
/chats
/my id"""

def handle_admin(uid, text):
    contacts = load_contacts()
    admin_ids = contacts.get("admin_ids", [])
    if not admin_ids:
        contacts["admin_ids"] = [uid]
        save_contacts(contacts)
        admin_ids = [uid]
    tl = text.lower().strip()
    if tl == "/my id": return "Your LINE user ID:\n" + uid
    if tl.startswith("/register "): return handle_register(uid, text, contacts)
    if tl == "/chats":
        sessions = load_sessions()
        hs = sessions.get(uid)
        if hs and hs.get("type") == "helper": return None  # handled separately with flex
        return "You have no active conversations."
    if uid not in admin_ids: return "No admin access.\nYour ID: " + uid
    if tl in ["/admin", "/help"]: return ADMIN_HELP
    if tl == "/list admins": return "Admins:\n" + "\n".join(admin_ids)
    if tl.startswith("/add admin "):
        nid = text[11:].strip()
        if nid not in contacts["admin_ids"]: contacts["admin_ids"].append(nid)
        save_contacts(contacts)
        return "Added admin: " + nid
    if tl.startswith("/add counselor "):
        parts = text[15:].split("|")
        if len(parts) < 3: return "Format: /add counselor Name | Role | Email"
        e = {"name": parts[0].strip(), "role": parts[1].strip(), "email": parts[2].strip(), "user_id": ""}
        contacts["counselors"].append(e); save_contacts(contacts)
        return "Added: " + e["name"] + "\nThey must: /register counselor " + e["name"]
    if tl.startswith("/add tutor "):
        parts = text[11:].split("|")
        if len(parts) < 3: return "Format: /add tutor Name | Role | Subjects"
        e = {"name": parts[0].strip(), "role": parts[1].strip(), "user_id": "", "subjects": [s.strip() for s in parts[2].split(",")]}
        contacts["tutors"].append(e); save_contacts(contacts)
        return "Added: " + e["name"] + "\nThey must: /register tutor " + e["name"]
    if tl.startswith("/add job "):
        parts = text[9:].split("|")
        if len(parts) < 4: return "Format: /add job Name | Company | Role | Industry"
        e = {"name": parts[0].strip(), "company": parts[1].strip(), "role": parts[2].strip(), "user_id": "", "industry": parts[3].strip()}
        contacts["job_contacts"].append(e); save_contacts(contacts)
        return "Added: " + e["name"] + "\nThey must: /register job " + e["name"]
    if tl.startswith("/remove counselor "):
        n = text[18:].strip(); b = len(contacts["counselors"])
        contacts["counselors"] = [c for c in contacts["counselors"] if c["name"].lower() != n.lower()]
        save_contacts(contacts); return ("Removed: " + n) if len(contacts["counselors"]) < b else ("Not found: " + n)
    if tl.startswith("/remove tutor "):
        n = text[14:].strip(); b = len(contacts["tutors"])
        contacts["tutors"] = [t for t in contacts["tutors"] if t["name"].lower() != n.lower()]
        save_contacts(contacts); return ("Removed: " + n) if len(contacts["tutors"]) < b else ("Not found: " + n)
    if tl.startswith("/remove job "):
        n = text[12:].strip(); b = len(contacts["job_contacts"])
        contacts["job_contacts"] = [j for j in contacts["job_contacts"] if j["name"].lower() != n.lower()]
        save_contacts(contacts); return ("Removed: " + n) if len(contacts["job_contacts"]) < b else ("Not found: " + n)
    if tl.startswith("/set scholarship form "):
        contacts["scholarship"]["google_form_url"] = text[22:].strip(); save_contacts(contacts); return "Updated."
    if tl.startswith("/set scholarship doc "):
        contacts["scholarship"]["google_doc_url"] = text[21:].strip(); save_contacts(contacts); return "Updated."
    return "Unknown command. /admin for help."

def handle_register(uid, text, contacts):
    tl = text.lower().strip()
    if tl.startswith("/register counselor "):
        name = text[20:].strip()
        for c in contacts["counselors"]:
            if c["name"].lower() == name.lower():
                c["user_id"] = uid; save_contacts(contacts)
                return "Registered as counselor: " + name
        return "Not found: '" + name + "'"
    if tl.startswith("/register tutor "):
        name = text[16:].strip()
        for t in contacts["tutors"]:
            if t["name"].lower() == name.lower():
                t["user_id"] = uid; save_contacts(contacts)
                return "Registered as tutor: " + name
        return "Not found: '" + name + "'"
    if tl.startswith("/register job "):
        name = text[14:].strip()
        for j in contacts["job_contacts"]:
            if j["name"].lower() == name.lower():
                j["user_id"] = uid; save_contacts(contacts)
                return "Registered as job contact: " + name
        return "Not found: '" + name + "'"
    if tl == "/register scholarship":
        contacts["scholarship"]["contact_user_id"] = uid; save_contacts(contacts)
        return "Registered as scholarship contact!"
    return "Usage: /register counselor YourName"


# ─── Main handler ────────────────────────────────────────────────

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
        if tl == "/chats":
            hs = sessions.get(uid)
            if hs and hs.get("type") == "helper":
                reply(event.reply_token, build_inbox(hs))
                return
        r = handle_admin(uid, text)
        if r: reply(event.reply_token, T(r))
        return

    # 2. Student relay
    us = sessions.get(uid)
    if us and us.get("type") == "student":
        if tl == "exit":
            name = us["connected_name"]
            disconnect_student(uid, sessions)
            reply(event.reply_token, build_ended_card(name))
            return
        helper_id = us["connected_to"]
        student_name = get_display_name(uid)
        cat = us.get("category", "tutor")
        color = {"counselor": C["blue"], "tutor": C["green"], "job": C["orange"], "scholarship": C["red"]}.get(cat, C["blue"])
        try:
            hs = sessions.get(helper_id)
            if hs and hs.get("type") == "helper":
                hs["replying_to"] = uid; save_sessions(sessions)
            push(helper_id, build_message_card(student_name, text, color))
            reply(event.reply_token, build_sent_card(us["connected_name"]))
        except Exception as e:
            reply(event.reply_token, T("Could not deliver: " + str(e)[:80]))
        return

    # 3. Helper relay
    if us and us.get("type") == "helper":
        convos = us.get("conversations", {})
        if tl.startswith("exit "):
            target_name = text[5:].strip()
            for sid, info in convos.items():
                if info["name"].lower() == target_name.lower():
                    try: push(sid, build_ended_card(get_display_name(uid)))
                    except: pass
                    disconnect_student(sid, sessions)
                    reply(event.reply_token, build_ended_card(target_name))
                    return
            reply(event.reply_token, T("No chat with '" + target_name + "'. Type /chats"))
            return
        if tl == "exit":
            if len(convos) == 1:
                sid = list(convos.keys())[0]; sname = convos[sid]["name"]
                try: push(sid, build_ended_card(get_display_name(uid)))
                except: pass
                disconnect_student(sid, sessions)
                reply(event.reply_token, build_ended_card(sname))
                return
            reply(event.reply_token, T("Multiple chats. Use: exit Name\nOr /chats to see all."))
            return
        if text.startswith("@"):
            space = text.find(" ", 1)
            if space > 0:
                tname = text[1:space].strip(); msg = text[space+1:].strip()
                for sid, info in convos.items():
                    if info["name"].lower() == tname.lower() and msg:
                        hname = get_display_name(uid)
                        cat = info.get("category", "tutor")
                        color = {"counselor": C["blue"], "tutor": C["green"], "job": C["orange"], "scholarship": C["red"]}.get(cat, C["blue"])
                        try:
                            push(sid, build_message_card(hname, msg, color))
                            us["replying_to"] = sid; save_sessions(sessions)
                            reply(event.reply_token, build_sent_card(tname))
                        except Exception as e:
                            reply(event.reply_token, T("Error: " + str(e)[:80]))
                        return
                reply(event.reply_token, T("No chat with that name. /chats to see all."))
                return
        if tl in ["hi", "hello", "menu", "help", "hey", "back"]:
            reply(event.reply_token, build_inbox(us))
            return
        rt = us.get("replying_to")
        if rt and rt in convos:
            tname = convos[rt]["name"]
            hname = get_display_name(uid)
            cat = convos[rt].get("category", "tutor")
            color = {"counselor": C["blue"], "tutor": C["green"], "job": C["orange"], "scholarship": C["red"]}.get(cat, C["blue"])
            try:
                push(rt, build_message_card(hname, text, color))
                reply(event.reply_token, build_sent_card(tname))
            except Exception as e:
                reply(event.reply_token, T("Error: " + str(e)[:80]))
            return
        reply(event.reply_token, [T("Not sure who to reply to."), build_inbox(us)])
        return

    # 4. Picking
    if uid in pending:
        cat = pending[uid]["category"]
        avail = get_available(cat, contacts)
        if tl == "exit":
            del pending[uid]; save_pending(pending)
            reply(event.reply_token, build_main_menu())
            return
        try:
            idx = int(text) - 1
            if 0 <= idx < len(avail):
                p = avail[idx]; del pending[uid]; save_pending(pending)
                connect_users(uid, p["user_id"], p["name"], cat, sessions)
                reply(event.reply_token, T("Connecting..."))
                return
            reply(event.reply_token, T("Pick a valid number or 'exit'."))
            return
        except ValueError:
            reply(event.reply_token, T("Reply with a number or 'exit'."))
            return

    # 5. Menu
    if tl in ["hi", "hello", "menu", "start", "help", "hey", "back"]:
        reply(event.reply_token, build_main_menu())
        return

    # 6. Options
    def try_connect(cat):
        avail = get_available(cat, contacts)
        if not avail:
            reply(event.reply_token, T("No one available yet. Type 'hi' for menu."))
            return
        if len(avail) == 1:
            connect_users(uid, avail[0]["user_id"], avail[0]["name"], cat, sessions)
            reply(event.reply_token, T("Connecting..."))
            return
        picker = build_person_picker_flex(cat, contacts)
        if picker:
            pending[uid] = {"category": cat}; save_pending(pending)
            reply(event.reply_token, picker)

    if text in ["1"] or "counselor" in tl or "admission" in tl: try_connect("counselor"); return
    if text in ["2"] or "tutor" in tl or "education" in tl or "test" in tl or "study" in tl: try_connect("tutor"); return
    if text in ["3"] or "scholarship" in tl: reply(event.reply_token, build_scholarship_messages(contacts)); return
    if tl == "connect":
        si = contacts.get("scholarship", {})
        sid, sn = si.get("contact_user_id", ""), si.get("contact_name", "")
        if sid:
            connect_users(uid, sid, sn, "scholarship", sessions)
            reply(event.reply_token, T("Connecting..."))
        else: reply(event.reply_token, T("Scholarship contact not registered yet."))
        return
    if text in ["4"] or "job" in tl or "work" in tl or "career" in tl: try_connect("job"); return

    reply(event.reply_token, [T("Welcome!"), build_main_menu()])

@app.route("/", methods=["GET"])
def health():
    return "Student Support Hub Bot is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
