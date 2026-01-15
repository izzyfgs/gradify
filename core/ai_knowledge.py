# core/ai_knowledge.py
import re
from typing import Optional, Dict, List

SUPPORT_EMAIL = "israelmalachy21@gmail.com"

FALLBACK_REPLY = (
    "Thanks for your question — I’m not fully sure yet.\n\n"
    "Please tap **Generate a Ticket** so I can help you properly."
)

KB: List[Dict] = [
    {"keywords": ["good morning", "morning", "gm"], "answer": "Good morning 😊 How can I help you with Gradify today?"},
    {"keywords": ["good afternoon", "afternoon"], "answer": "Good afternoon 😊 What can I help you with today?"},
    {"keywords": ["good evening", "evening"], "answer": "Good evening 😊 How can I assist you today?"},
    {"keywords": ["hi", "hello", "hey"], "answer": "Hi 😊 Welcome to Gradify. What do you need help with?"},

    {"keywords": ["add score", "save score", "new score"], "answer": "To save a score: tap **Add New**, choose the subject, enter year + correct/total, then tap Save."},
    {"keywords": ["score not showing", "didn't show", "not reflect", "not reflected"], "answer": "First refresh the page. If it still doesn’t show, confirm you saved successfully and that the subject matches your selected subjects."},
    {"keywords": ["choose subjects", "setup subjects", "select subjects"], "answer": "Tap **Add New** (first time) → choose your subjects → tap **Save Subjects**."},
    {"keywords": ["change subjects", "edit subjects", "update subjects"], "answer": "Yes. You can re-open subject setup and update your subjects. Your dashboard will adjust automatically."},

    {"keywords": ["average wrong", "average is wrong", "wrong average"], "answer": "Your average should be the mean of all saved score percentages. If it looks wrong, share your percentages and I’ll confirm the correct value."},
    {"keywords": ["streak", "study streak"], "answer": "Your streak counts how many days in a row you saved at least one score."},
    {"keywords": ["break streak", "streak reset"], "answer": "If you miss a day without saving a score, the streak resets."},

    {"keywords": ["view scores", "performance history", "history"], "answer": "Tap **View Scores** to see all your saved scores."},
    {"keywords": ["grouped by subject", "group scores", "section by subject"], "answer": "Scores should appear in sections like **Maths:**, **English:**, etc. If yours are not grouped, we’ll enable grouped display."},

    {"keywords": ["edit score", "update score"], "answer": "Go to **View Scores**, tap the three dots (⋮) for that score, then choose **Edit**."},
    {"keywords": ["delete score", "remove score"], "answer": "Go to **View Scores**, tap (⋮) then select **Delete** (shown in red)."},
    {"keywords": ["deleted by mistake", "undo delete"], "answer": "There’s no undo yet. If you remember the score, you can re-add it using **Add New**."},

    {"keywords": ["best subject", "what is best subject"], "answer": "Best Subject is the subject where your performance is highest based on your saved scores."},
    {"keywords": ["best subject showing number", "best subject is 17"], "answer": "That’s a bug. Best Subject should display a subject name (e.g., “Further Mathematics”), not a number."},

    {"keywords": ["same subject", "multiple scores", "many scores"], "answer": "You can save multiple scores per subject. If your system blocks duplicates per year, use another year or edit the existing entry."},
    {"keywords": ["can't login", "cannot login", "login failed"], "answer": "Confirm your username/password. If you still can’t log in, generate a ticket and include your username."},
    {"keywords": ["forgot password", "reset password", "password"], "answer": "Password reset can be handled via support for now. Tap **Generate Ticket** and include your username/email."},
    {"keywords": ["change username", "edit username"], "answer": "Not yet. Usernames are unique. We can add username change later with verification."},

    {"keywords": ["profile picture", "avatar", "my photo"], "answer": "If your avatar appears shared across accounts, it’s being stored globally. We’ll store it per-user (or in the database) to fix that."},

    {"keywords": ["contact support", "support", "help"], "answer": "You can contact support via WhatsApp, email, phone call, or Chat with AI."},
    {"keywords": ["mobile", "phone view", "responsive"], "answer": "Yes — we’ll redesign Gradify to be mobile-first so the UI looks clean and readable on phones."},
    {"keywords": ["blank page", "not loading", "page not working"], "answer": "Refresh first. If it still fails, check your internet connection. If it continues, generate a ticket."},

    {"keywords": ["what is gradify", "about gradify", "what does gradify do"], "answer": "Gradify helps you track your practice scores, streaks, averages, and subject performance over time."},
    {"keywords": ["export", "download scores", "pdf", "csv"], "answer": "Export isn’t available yet, but we can add PDF/CSV export later."},
    {"keywords": ["data safe", "is my data safe", "privacy"], "answer": "Your scores are stored in the database under your account. Keep your password secure and don’t share it."},

    {"keywords": ["add new not working", "add new not directing", "doesn't direct"], "answer": "If you have no subjects yet, Add New must take you to choose subjects first. If it doesn’t, we’ll fix the redirect logic."},
    {"keywords": ["improve average", "increase score", "improve"], "answer": "Save practice consistently and focus on your weakest subject first. Small daily improvement wins."},
]

def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text

def find_answer(user_message: str) -> Optional[str]:
    msg = _normalize(user_message)
    if not msg:
        return "Please type a question and I’ll help you."

    for item in KB:
        for kw in item["keywords"]:
            if _normalize(kw) in msg:
                return item["answer"]

    # light token matching for short queries
    tokens = set(re.findall(r"[a-z0-9]+", msg))
    for item in KB:
        for kw in item["keywords"]:
            kw_tokens = set(re.findall(r"[a-z0-9]+", _normalize(kw)))
            if kw_tokens and kw_tokens.issubset(tokens):
                return item["answer"]

    return None

def build_response(user_message: str) -> Dict:
    answer = find_answer(user_message)
    if answer:
        return {"ok": True, "type": "answer", "reply": answer}

    return {
        "ok": True,
        "type": "fallback",
        "reply": FALLBACK_REPLY,
        "ticket": {
            "label": "Generate a Ticket",
            "mailto": (
                f"mailto:{SUPPORT_EMAIL}"
                f"?subject=Gradify%20Support%20Ticket"
                f"&body=Hi%20Gradify%20Support,%0A%0AMy%20question:%20{user_message}%0A%0AThanks!"
            ),
        },
    }
