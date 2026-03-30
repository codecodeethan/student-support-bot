# 🎓 Student Support Hub — LINE Chatbot
## Deployment & Setup Guide

---

## What This Bot Does

A LINE chatbot that connects at-risk students to four types of support:

| # | Feature | What Happens |
|---|---------|-------------|
| 1 | **Counselor Help** | Shows your school's Thai counselor contact cards |
| 2 | **Education Support** | Shows your tutor team with subjects they cover |
| 3 | **Scholarship Info** | Shows scholarship details + Google Form/Doc buttons |
| 4 | **Job Connections** | Shows job fair contacts organized by industry |

Users type `hi`, `menu`, or `สวัสดี` to see the menu, then pick 1-4.

You (and anyone you add as admin) can **add/remove contacts directly in LINE chat** using commands like `/add tutor Pim | Math Help | @pim | Math, Physics`.

---

## Step 1: Create a LINE Bot Channel (5 minutes)

1. Go to [LINE Developers Console](https://developers.line.biz/console/)
2. Log in with your LINE account
3. Click **Create a new provider** → name it (e.g., "Student Support Hub")
4. Click **Create a Messaging API channel**
   - Channel name: `Student Support Hub`
   - Channel description: `Connecting students to counselors, tutors, scholarships & jobs`
   - Category: Education
   - Subcategory: School
5. In your channel settings, go to the **Messaging API** tab:
   - Under **Channel access token**, click **Issue** → copy and save this token
   - Under **Webhook settings**, you'll add your URL after deploying (Step 3)
6. Go to the **Basic settings** tab:
   - Copy your **Channel secret**

**Save both values — you'll need them in Step 3.**

---

## Step 2: Set Up Your Google Form (5 minutes)

1. Go to [Google Forms](https://forms.google.com)
2. Create a scholarship application form with fields like:
   - Student name
   - School / Grade
   - Family situation
   - Why they need scholarship support
   - Contact LINE ID
3. Copy the form URL
4. (Optional) Create a Google Doc with scholarship details/requirements
5. You'll paste these URLs into `contacts.json` or use the admin commands later

---

## Step 3: Deploy to Railway (10 minutes)

### Why Railway?
- Free tier (500 hours/month — enough for a chatbot)
- Deploys from GitHub in one click
- Automatic HTTPS (required by LINE)
- No credit card needed to start

### Steps:

1. **Push code to GitHub:**
   ```bash
   cd line-chatbot
   git init
   git add .
   git commit -m "Initial chatbot"
   # Create a repo on GitHub, then:
   git remote add origin https://github.com/YOUR_USERNAME/student-support-bot.git
   git branch -M main
   git push -u origin main
   ```

2. **Deploy on Railway:**
   - Go to [railway.app](https://railway.app) → Sign in with GitHub
   - Click **New Project** → **Deploy from GitHub repo**
   - Select your `student-support-bot` repo
   - Go to your project → **Variables** tab → Add:
     ```
     LINE_CHANNEL_SECRET = (paste your channel secret)
     LINE_CHANNEL_ACCESS_TOKEN = (paste your access token)
     ```
   - Railway will auto-deploy. Click **Settings** → **Generate Domain** to get your URL

3. **Connect to LINE:**
   - Copy your Railway URL (e.g., `https://student-support-bot-production.up.railway.app`)
   - Go back to LINE Developers Console → Messaging API tab
   - Set **Webhook URL** to: `https://YOUR-RAILWAY-URL/callback`
   - Click **Verify** — it should succeed
   - Turn **Use webhook** ON
   - Turn **Auto-reply messages** OFF (in LINE Official Account settings)

---

## Step 4: Configure Your Bot

### Option A: Edit contacts.json directly
Edit the `contacts.json` file with your real contacts, push to GitHub, Railway auto-redeploys.

### Option B: Use admin commands in LINE (recommended)
Message your bot with any `/` command — the **first person to send an admin command becomes the admin**.

#### Available Commands:

```
/admin                           — Show all commands
/add counselor Name | Role | @line_id | email@school.th
/add tutor Name | Role | @line_id | Math, English
/add job Name | Company | Position | @line_id | Industry
/remove counselor Name
/remove tutor Name
/remove job Name
/set scholarship form https://docs.google.com/forms/...
/set scholarship doc https://docs.google.com/document/...
/add admin Uxxxxxxxxxxxxxxxxx    — Add another admin by user ID
/list admins
```

#### Example — Adding Your Team:
```
/add tutor Pim | SAT Math Tutor | @pim_tutor | Math, SAT Prep
/add tutor Fern | English Support | @fern99 | English, IELTS
/add counselor Ajarn Nida | University Admissions | @ajarn_nida | nida@ris.ac.th
/add job Khun Siri | SCB | HR Manager | @siri_scb | Banking & Finance
/set scholarship form https://docs.google.com/forms/d/e/1FAIpQLSf.../viewform
```

---

## How Users Interact

```
Student:  สวัสดี
Bot:      [Shows beautiful menu card with 4 options]

Student:  3
Bot:      "Great that you're looking into scholarships!"
          [Shows scholarship card with Google Form button]

Student:  job
Bot:      "Here are contacts from recent job fairs..."
          [Shows carousel of job contact cards]
```

The bot responds to:
- Numbers: `1`, `2`, `3`, `4`
- Keywords: `counselor`, `admission`, `tutor`, `study`, `test`, `scholarship`, `job`, `career`
- Thai keywords: `ที่ปรึกษา`, `สอน`, `ทุน`, `งาน`
- Greetings: `hi`, `hello`, `menu`, `start`, `สวัสดี`, `เมนู`

---

## Folder Structure

```
line-chatbot/
├── app.py              ← Main bot logic (all 4 features + admin commands)
├── contacts.json       ← Your editable contact data
├── requirements.txt    ← Python dependencies
├── Procfile            ← Tells Railway how to run the app
└── README.md           ← This file
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Webhook verification fails | Make sure URL ends with `/callback` |
| Bot doesn't reply | Check that auto-reply is OFF in LINE Official Account |
| "Invalid signature" error | Double-check your `LINE_CHANNEL_SECRET` env variable |
| Railway deploy fails | Check logs: `railway logs` — usually a typo in requirements |
| Contacts reset after redeploy | Normal on Railway free tier — use a database for persistence (ask me to upgrade!) |

---

## Future Upgrades

When you're ready, I can help you add:
- **Thai language support** — full bilingual menu
- **Database storage** (PostgreSQL) — so contacts persist across deploys
- **Rich menu** — the persistent bottom menu in LINE with visual buttons
- **Analytics** — track how many students use each feature
- **Automated follow-up** — bot checks in with students after initial contact

---

Built for Ethan's dropout prevention initiative 🇹🇭
