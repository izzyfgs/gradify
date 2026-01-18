from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.shortcuts import render, redirect
from .models import UserSubject, Score
import json
from difflib import SequenceMatcher
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import SupportFAQ
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.timezone import now
from .models import UserSubject, Score, AIConversation, AIMessage



from django.core.mail import send_mail
from django.conf import settings

def register_view(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        if not all([first_name, last_name, username, email, password]):
            messages.error(request, "Please fill in all fields.")
            return render(request, "register.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "That username is already taken.")
            return render(request, "register.html")

        if User.objects.filter(email=email).exists():
            messages.error(request, "That email is already in use.")
            return render(request, "register.html")

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
            )
            user.first_name = first_name
            user.last_name = last_name
            user.save()

            # --- EMAIL LOGIC START ---
            
            # 1. Send Welcome Email to the Student
            send_mail(
                subject='Welcome to Gradify!',
                message=f'Hi {first_name}, your account is ready. Start tracking your scores and crush your goals!',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True, # Prevents site crash if email server is down
            )

            # 2. Send Alert to You (The Admin)
            send_mail(
                subject='🚀 New User Registered on Gradify',
                message=f'New student joined!\nName: {first_name} {last_name}\nUsername: {username}\nEmail: {email}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['your-personal-email@gmail.com'], # Put your email here
                fail_silently=True,
            )
            
            # --- EMAIL LOGIC END ---

        except IntegrityError:
            messages.error(request, "Something went wrong. Try another username.")
            return render(request, "register.html")

        messages.success(request, "Registration successful! Please login.")
        return redirect("login")

    return render(request, "register.html")

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
def login_view(request):
    if request.method == "POST":
        # You are likely missing these two lines:
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Now 'username' is defined, so this line will work:
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            # Optional: add an error message if login fails
            return render(request, "login.html", {"error": "Invalid credentials"})
            
    return render(request, "login.html")

from django.contrib.auth.decorators import login_required
from .models import UserSubject, Score


ALL_SUBJECTS = [
    # Sciences
    "Mathematics", 
    "Further Mathematics", 
    "Physics", 
    "Chemistry", 
    "Biology", 
    "Agricultural Science",
    
    # Arts & Humanities
    "English", 
    "Literature", 
    "History", 
    "CRS",  # Christian Religious Studies
    "IRS",  # Islamic Religious Studies
    "Civic Education",
    
    # Social Sciences & Commercial
    "Economics", 
    "Government", 
    "Geography", 
    "Commerce", 
    "Accounting"
]
@login_required(login_url="login")
def setup_subjects_view(request):
    if request.method == "POST":
        chosen = request.POST.getlist("subjects")

        if not chosen:
            return render(request, "setup_subjects.html", {
                "all_subjects": ALL_SUBJECTS,
                "error": "Please select at least 1 subject."
            })

        # clear previous + save new
        UserSubject.objects.filter(user=request.user).delete()
        UserSubject.objects.bulk_create([
            UserSubject(user=request.user, name=s) for s in chosen
        ])

        return redirect("dashboard")

    return render(request, "setup_subjects.html", {"all_subjects": ALL_SUBJECTS})




from django.contrib import messages
from .forms import ScoreForm
from .models import Score

@login_required


@login_required(login_url="login")
def add_score_view(request):
    # ✅ If user has not chosen subjects yet, force them to setup first
    if not request.user.subjects.exists():
        return redirect("setup_subjects")

    if request.method == "POST":
        form = ScoreForm(request.POST, user=request.user) # ✅ important
        if form.is_valid():
            score = form.save(commit=False)
            score.user = request.user
            score.save()
            return redirect("dashboard")
    else:
        form = ScoreForm(user=request.user) # ✅ important

    return render(request, "add_score.html", {"form": form})

@login_required
def view_scores_view(request):
    scores = Score.objects.filter(user=request.user)
    return render(request, "view_scores.html", {"scores": scores})


@login_required
def help_support_view(request):
    return render(request, "help_support.html")
# -----------------------------
# AI "Knowledge Base" (30 items)
# -----------------------------
AI_KB = {
    "hello": "Hi 😊 Welcome to Gradify! How can I help you today?",
    "hi": "Hey! 😊 What can I help you with in Gradify?",
    "good morning": "Good morning ☀️ Hope you’re doing well! What do you need help with?",
    "good afternoon": "Good afternoon 😊 How can I help you today?",
    "good evening": "Good evening 🌙 How can I help you today?",

    "how do i add a score": "To add a score: Dashboard → Add New → choose subject → enter year, correct, total → Save.",
    "i can't add score": "Okay — what exactly happens when you tap Add New? Does it show an error or does it not open?",
    "my subjects are not showing": "That usually means your subjects haven’t been saved yet. Go to Add New → Choose Subjects → Save Subjects.",
    "how do i choose subjects": "Tap Add New for the first time → choose your subjects → tap Save Subjects.",
    "why is my average wrong": "Your average is calculated from all saved scores. If it looks wrong, tell me the scores you saved and I’ll check what’s happening.",

    "how do i edit score": "Go to View Scores → tap the 3 dots on the score → choose Edit.",
    "how do i delete score": "Go to View Scores → tap the 3 dots → Delete (it’s red).",
    "i forgot my password": "If you forgot your password, tell the admin via email and we’ll help you reset it.",
    "how do i logout": "Tap Logout on the sidebar. It will return you to the login page.",
    "what is study streak": "Study streak counts how many days in a row you saved at least one score.",

    "why is best subject wrong": "Best subject is based on your highest percentage score. If it looks wrong, tell me the subject + percentage showing.",
    "my dashboard is blank": "If your dashboard is blank, it may be because you haven’t selected subjects yet. Tap Add New to set them up.",
    "i can't login": "If login fails, confirm your username (not email) and password are correct. What exact message do you see?",
    "i can't register": "If registration fails, tell me the error shown on the register page.",
    "csrf token missing": "That happens when {% csrf_token %} is missing in your form. Add it inside the <form> tag.",

    "page not found 404": "That usually means the URL route is missing in urls.py. Tell me which page shows 404.",
    "bad request 400": "That often happens due to incorrect ALLOWED_HOSTS or a malformed request. Tell me what URL you visited and your ALLOWED_HOSTS setting.",
    "no reverse match": "That means your template is trying to use {% url 'name' %} but that name doesn’t exist in urls.py.",

    "contact": "You can reach support via WhatsApp, email, or phone in the Help & Support page.",
    "email": "You can email support at israelmalachy21@gmail.com",
    "whatsapp": "You can WhatsApp support here: wa.me/22955278109",
    "phone": "You can call support at +2290155278109",

    "what is gradify": "Gradify helps you track scores, calculate performance, and stay consistent with your learning.",
    "is my data saved": "Yes — your scores and AI chats are saved to your account in the database.",
    "does gradify work on phone": "Yes — Gradify is designed to work on mobile. If anything looks off, tell me your screen size/device.",

    "help": "Tell me what you’re trying to do, and what went wrong. I’ll guide you step-by-step.",
    "thanks": "You’re welcome 😊 Want to continue or need anything else?",
    "thank you": "Anytime 😊 What else can I help you with?",
}


def ai_realistic_reply(user_text: str) -> dict:
    """
    Returns dict:
      { "text": "...", "needs_ticket": bool }
    """
    t = (user_text or "").strip().lower()

    # Exact match / contains match
    for key, answer in AI_KB.items():
        if key in t:
            return {"text": answer, "needs_ticket": False}

    # Realistic clarification for vague messages
    vague = ["it doesn't work", "not working", "help me", "problem", "issue", "error", "stuck", "why"]
    if any(v in t for v in vague) or len(t) < 6:
        return {
            "text": (
                "I’m not 100% sure what you mean yet 😅\n\n"
                "Quick question so I can help properly:\n"
                "1) Which page are you on? (Dashboard / Add Score / View Scores / Login)\n"
                "2) What did you click?\n"
                "3) What happened after (error message / nothing / redirected)?"
            ),
            "needs_ticket": False
        }

    # Ticket fallback
    return {
        "text": (
            "Thanks — I understand, but this looks like something that may need admin support.\n\n"
            "Tap **Generate Ticket** and send the details, including a screenshot if possible."
        ),
        "needs_ticket": True
    }


@login_required
def ai_chat_view(request):
    # Get or create ONE active conversation per user
    convo, _ = AIConversation.objects.get_or_create(user=request.user)

    msgs = convo.messages.all()
    return render(request, "ai_chat.html", {"messages": msgs})


@login_required
@require_POST
def ai_chat_send(request):
    user_text = request.POST.get("message", "").strip()

    if not user_text:
        return JsonResponse({"ok": False, "error": "Empty message."}, status=400)

    convo, _ = AIConversation.objects.get_or_create(user=request.user)

    # Save user msg
    AIMessage.objects.create(conversation=convo, sender="user", text=user_text)

    # Generate reply
    reply = ai_realistic_reply(user_text)

    # Save AI msg
    AIMessage.objects.create(conversation=convo, sender="ai", text=reply["text"])

    return JsonResponse({
        "ok": True,
        "reply": reply["text"],
        "needs_ticket": reply["needs_ticket"]
    })


def logout_view(request):
    logout(request)
    return redirect("login")

from datetime import date, timedelta
from .models import Score

def get_streak(user):
    # Get all unique dates when the user saved a score, sorted newest first
    dates = Score.objects.filter(user=user).dates('created_at', 'day', order='DESC')
    
    if not dates:
        return 0

    streak = 0
    today = date.today()
    check_date = today

    # If they haven't posted today, check if they posted yesterday to keep streak alive
    if dates[0] < today:
        if dates[0] == today - timedelta(days=1):
            check_date = today - timedelta(days=1)
        else:
            return 0 # Streak broken

    for d in dates:
        if d == check_date:
            streak += 1
            check_date -= timedelta(days=1) # Move back 1 day to check previous
        else:
            break
    return streak


# In views.py
@login_required
def admin_overview(request):
    if not request.user.is_staff:
        return redirect('dashboard') # Keep regular students out!
        
    new_users = User.objects.all().order_by('-date_joined')[:10]
    return render(request, 'admin_view.html', {'new_users': new_users})

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import UserSubject, Score
from .forms import ScoreForm  # you already use this form in add_score_view


@login_required
def view_scores_view(request):
    """
    Groups scores by the user's selected subjects.
    Shows subject sections even if empty.
    """
    user_subjects = list(
        UserSubject.objects.filter(user=request.user).order_by("name")
    )

    # Pull all scores for this user (newest first as your model ordering already does)
    scores = list(Score.objects.filter(user=request.user))

    # Build a dict: { "Mathematics": [Score, Score], "English": [] ... }
    grouped = {sub.name: [] for sub in user_subjects}

    # Put scores into their subject bucket
    for s in scores:
        if s.subject in grouped:
            grouped[s.subject].append(s)
        else:
            # In case user has a score saved for a subject that isn't in setup anymore
            grouped.setdefault("Other", []).append(s)

    context = {
        "subjects": user_subjects,          # list of UserSubject objects
        "grouped_scores": grouped,          # dict subject_name -> list[Score]
    }
    return render(request, "view_scores.html", context)


@login_required
def edit_score_view(request, score_id):
    score = get_object_or_404(Score, id=score_id, user=request.user)

    if request.method == "POST":
        form = ScoreForm(request.POST, instance=score, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Score updated successfully.")
            return redirect("view_scores")
    else:
        form = ScoreForm(instance=score, user=request.user)

    return render(request, "edit_score.html", {"form": form, "score": score})


@login_required
def delete_score_view(request, score_id):
    score = get_object_or_404(Score, id=score_id, user=request.user)

    if request.method == "POST":
        score.delete()
        messages.success(request, "Score deleted successfully.")
        return redirect("view_scores")

    # If someone opens delete link via GET, send them back safely
    return redirect("view_scores")


@require_POST
@csrf_exempt  # we’ll still send CSRF from frontend, but this prevents random CSRF crashes during testing
def support_chat_api(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"reply": "Sorry—something went wrong reading your message."}, status=400)

    user_msg = (data.get("message") or "").strip()
    if not user_msg:
        return JsonResponse({"reply": "Please type a message so I can help you."})

    text = user_msg.lower()

    faqs = SupportFAQ.objects.filter(is_active=True)

    best = None
    best_score = 0.0

    # Match method:
    # 1) keyword hit gives strong score
    # 2) fuzzy similarity as backup
    for faq in faqs:
        score = 0.0

        # Keyword match
        kw_list = [k.strip().lower() for k in (faq.keywords or "").split(",") if k.strip()]
        for kw in kw_list:
            if kw and kw in text:
                score += 0.35  # each keyword hit boosts confidence

        # Fuzzy match (question similarity)
        sim = SequenceMatcher(None, text, faq.question.lower()).ratio()
        score += sim * 0.75

        if score > best_score:
            best_score = score
            best = faq

    # Confidence threshold (tweak if needed)
    if best and best_score >= 0.65:
        return JsonResponse({"reply": best.answer})

    # Fallback → professional + ticket button
    fallback = (
        "Thanks for reaching out. I’m not fully sure I understood your request.\n\n"
        "Please tap **Create a Ticket** so I can help you directly."
    )

    return JsonResponse({
        "reply": fallback,
        "show_ticket": True
    })

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import UserSubject, Score
from .forms import ScoreForm


@login_required
def view_scores_view(request):
    # All subjects the user picked (ALWAYS show them, even if no scores yet)
    subjects = list(
        UserSubject.objects.filter(user=request.user)
        .values_list("name", flat=True)
    )

    # Alphabetical order (your choice: option 2)
    subjects_sorted = sorted(subjects, key=lambda x: x.lower())

    # All scores
    scores = Score.objects.filter(user=request.user)

    # Group scores by subject name
    grouped = {name: [] for name in subjects_sorted}
    for sc in scores:
        # Ensure we only group into subjects they selected
        if sc.subject in grouped:
            grouped[sc.subject].append(sc)

    context = {
        "grouped_scores": grouped,        # dict: { "English": [Score, Score], ... }
        "subjects_sorted": subjects_sorted # for headings
    }
    return render(request, "view_scores.html", context)


@login_required
def edit_score_view(request, score_id):
    score = get_object_or_404(Score, id=score_id, user=request.user)

    if request.method == "POST":
        form = ScoreForm(request.POST, user=request.user, instance=score)
        if form.is_valid():
            form.save()
            messages.success(request, "Score updated successfully.")
            return redirect("view_scores")
    else:
        form = ScoreForm(user=request.user, instance=score)

    return render(request, "edit_score.html", {"form": form, "score": score})


@login_required
def delete_score_view(request, score_id):
    score = get_object_or_404(Score, id=score_id, user=request.user)

    if request.method == "POST":
        score.delete()
        messages.success(request, "Score deleted successfully.")
        return redirect("view_scores")

    # If someone tries GET, just send them back safely
    return redirect("view_scores")

import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from .ai_knowledge import build_response


@login_required
def ai_chat_view(request):
    # ✅ renders the separate chat page
    return render(request, "ai_chat.html")


@csrf_exempt
@require_POST
@login_required
def ai_support_api(request):
    """
    Receives JSON: { "message": "..." }
    Returns: { ok, type, reply, ticket? }
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
        user_message = (data.get("message") or "").strip()
    except Exception:
        return JsonResponse({"ok": False, "reply": "Invalid request."}, status=400)

    result = build_response(user_message)
    return JsonResponse(result)

import re
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import ChatMessage, UserSubject, Score





# ✅ Page that shows chat history
from django.contrib.auth.decorators import login_required

@login_required
def ai_chat_view(request):
    msgs = ChatMessage.objects.filter(user=request.user)
    unknown_count = ChatMessage.objects.filter(user=request.user, sender="ai", message__icontains="support ticket").count()
    return render(request, "ai_chat.html", {"messages": msgs, "unknown_count": unknown_count})


# ✅ Endpoint that receives user message + returns AI reply + saves both
@login_required
@require_POST
def ai_chat_send(request):
    user_text = request.POST.get("message", "").strip()
    if not user_text:
        return JsonResponse({"ok": False, "error": "Empty message."}, status=400)

    # Save user message
    ChatMessage.objects.create(user=request.user, sender="user", message=user_text)

    # How many times AI already got confused (simple metric)
    unknown_count = ChatMessage.objects.filter(user=request.user, sender="ai", message__icontains="support ticket").count()

    reply = ai_reply(user_text, unknown_count)

    if reply["type"] == "ticket":
        ai_text = reply["text"]
        ChatMessage.objects.create(user=request.user, sender="ai", message=ai_text)
        return JsonResponse({
            "ok": True,
            "type": "ticket",
            "reply": ai_text,
            "mailto": "mailto:israelmalachy21@gmail.com?subject=Gradify%20Support%20Ticket&body=Hi%20Israel,%20I%20need%20help%20with%20Gradify.%20Here%20is%20my%20issue:%20"
        })

    # Save AI reply
    ChatMessage.objects.create(user=request.user, sender="ai", message=reply["text"])

    return JsonResponse({"ok": True, "type": reply["type"], "reply": reply["text"]})

import json
import re
from difflib import SequenceMatcher

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.urls import reverse

from .models import FAQ, ChatSession, ChatMessage


SUPPORT_EMAIL = "israelmalachy21@gmail.com"
SUPPORT_PHONE = "+2290155278109"
SUPPORT_WHATSAPP = "https://wa.me/22955278109"


def _normalize(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def _is_greeting(msg: str) -> bool:
    m = _normalize(msg)
    greetings = [
        "hi", "hello", "hey", "good morning", "good afternoon", "good evening",
        "how are you", "yo", "hiya"
    ]
    return any(m == g or m.startswith(g + " ") for g in greetings)


def _greeting_reply(username: str) -> str:
    name = username or "there"
    return (
        f"Hi {name} 👋\n\n"
        "I’m Gradify Support AI. I can help with:\n"
        "• saving scores\n"
        "• viewing results\n"
        "• fixing dashboard stats\n"
        "• login/registration issues\n\n"
        "Tell me what you’re trying to do, and what went wrong."
    )


def _faq_best_match(user_msg: str):
    """
    Returns (faq_obj, score) using fuzzy similarity + keyword boost.
    """
    msg = _normalize(user_msg)
    if not msg:
        return None, 0.0

    faqs = FAQ.objects.filter(is_active=True)
    best = None
    best_score = 0.0

    msg_tokens = set(re.findall(r"[a-z0-9]+", msg))

    for f in faqs:
        q = _normalize(f.question)
        base = SequenceMatcher(None, msg, q).ratio()  # 0..1

        # keyword boost
        kw = _normalize(f.keywords)
        kw_tokens = set([t for t in re.findall(r"[a-z0-9]+", kw) if t])
        keyword_hits = len(msg_tokens.intersection(kw_tokens))

        score = base + min(0.20, keyword_hits * 0.04)  # cap boost

        if score > best_score:
            best_score = score
            best = f

    return best, best_score


def _clarify_question(user_msg: str) -> str:
    """
    Realistic clarification (instead of jumping to ticket).
    """
    return (
        "I want to help, but I’m not fully sure what you mean yet.\n\n"
        "Quick questions:\n"
        "1) What page were you on? (Dashboard / Add Score / View Scores / Login)\n"
        "2) What did you click?\n"
        "3) What happened after? (error message or nothing?)\n\n"
        "Reply with those 3 and I’ll guide you properly."
    )


def _ticket_message(user, last_user_msg: str) -> str:
    """
    Escalation with a mailto link (opens mail app on mobile).
    """
    subject = f"Gradify Support Ticket - {user.username}"
    body = (
        "Hi Israel,\n\n"
        "I need help with Gradify.\n\n"
        f"Username: {user.username}\n"
        f"Issue: {last_user_msg}\n\n"
        "What I tried:\n"
        "- \n\n"
        "Screenshot (if any):\n"
        "- \n\n"
        "Thanks."
    )
    # mailto -> opens email app (not browser)
    mailto = f"mailto:{SUPPORT_EMAIL}?subject={subject.replace(' ', '%20')}&body={body.replace(' ', '%20').replace('\\n', '%0A')}"
    return (
        "Thanks — I still can’t confidently answer that without risking a wrong fix.\n\n"
        "✅ Please generate a ticket so the developer can respond directly:\n"
        f"{mailto}\n\n"
        f"Or WhatsApp: {SUPPORT_WHATSAPP}\n"
        f"Or Call: {SUPPORT_PHONE}"
    )


def _assistant_reply(session: ChatSession, user_msg: str) -> str:
    # Greetings
    if _is_greeting(user_msg):
        session.awaiting_clarification = False
        session.last_unresolved_question = ""
        session.save(update_fields=["awaiting_clarification", "last_unresolved_question"])
        return _greeting_reply(session.user.username)

    # Try FAQ match
    faq, score = _faq_best_match(user_msg)

    # If good match, answer and reset clarify state
    if faq and score >= 0.58:
        session.awaiting_clarification = False
        session.last_unresolved_question = ""
        session.save(update_fields=["awaiting_clarification", "last_unresolved_question"])
        return faq.answer

    # If user previously unclear and still unclear -> escalate ticket
    if session.awaiting_clarification:
        session.awaiting_clarification = False
        session.save(update_fields=["awaiting_clarification"])
        return _ticket_message(session.user, session.last_unresolved_question or user_msg)

    # Otherwise ask clarification first (realistic)
    session.awaiting_clarification = True
    session.last_unresolved_question = user_msg[:1000]
    session.save(update_fields=["awaiting_clarification", "last_unresolved_question"])
    return _clarify_question(user_msg)


@login_required
def ai_chat_view(request):
    session, _ = ChatSession.objects.get_or_create(user=request.user)
    messages = session.messages.all()
    return render(request, "ai_chat.html", {"messages": messages})


@login_required
def ai_chat_send(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    user_msg = (payload.get("message") or "").strip()
    if not user_msg:
        return JsonResponse({"ok": False, "error": "Empty message"}, status=400)

    session, _ = ChatSession.objects.get_or_create(user=request.user)

    # save user message
    ChatMessage.objects.create(session=session, role="user", content=user_msg)

    # generate assistant reply
    reply = _assistant_reply(session, user_msg)

    # save assistant message
    ChatMessage.objects.create(session=session, role="assistant", content=reply)

    return JsonResponse({"ok": True, "reply": reply})


@login_required
def ai_chat_clear(request):
    session, _ = ChatSession.objects.get_or_create(user=request.user)
    session.messages.all().delete()
    session.awaiting_clarification = False
    session.last_unresolved_question = ""
    session.save(update_fields=["awaiting_clarification", "last_unresolved_question"])
    return redirect("ai_chat")

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone

from .models import (
    UserSubject, Score, UserProfile,
    Follow, Post, Like, Comment, Notification
)

from datetime import date, timedelta
from django.core.mail import send_mail
from django.conf import settings


# ✅ create profile automatically
def get_or_create_profile(user):
    profile, created = UserProfile.objects.get_or_create(user=user)
    return profile


def register_view(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        if not all([first_name, last_name, username, email, password]):
            messages.error(request, "Please fill in all fields.")
            return render(request, "register.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "That username is already taken.")
            return render(request, "register.html")

        if User.objects.filter(email=email).exists():
            messages.error(request, "That email is already in use.")
            return render(request, "register.html")

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
            )
            user.first_name = first_name
            user.last_name = last_name
            user.save()

            # ✅ create profile
            get_or_create_profile(user)

        except IntegrityError:
            messages.error(request, "Something went wrong. Try another username.")
            return render(request, "register.html")

        messages.success(request, "Registration successful! Please login.")
        return redirect("login")

    return render(request, "register.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("dashboard")

        messages.error(request, "Invalid username or password.")
        return redirect("login")

    return render(request, "login.html")


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


# ✅ STREAK
def get_streak(user):
    dates = Score.objects.filter(user=user).dates('created_at', 'day', order='DESC')
    if not dates:
        return 0

    streak = 0
    today = date.today()
    check_date = today

    if dates[0] < today:
        if dates[0] == today - timedelta(days=1):
            check_date = today - timedelta(days=1)
        else:
            return 0

    for d in dates:
        if d == check_date:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break
    return streak


# ✅ DASHBOARD

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import UserProfile, UserSubject, Score, Notification, UserSettings
from django.db.models import Q

# Helper to ensure profile exists
def get_or_create_profile(user):
    profile, created = UserProfile.objects.get_or_create(user=user)
    return profile

@login_required
def dashboard_view(request):
    profile = get_or_create_profile(request.user)
    settings_obj, _ = UserSettings.objects.get_or_create(user=request.user)
    user_subjects = UserSubject.objects.filter(user=request.user)
    
    # FIX: Only redirect on GET. This stops the "disappearing" bug during uploads.
    if not user_subjects.exists() and request.method == "GET":
        return redirect("setup_subjects")

    all_scores = Score.objects.filter(user=request.user).order_by('-created_at')
    subject_performances = []
    total_percentage_sum = 0
    subjects_with_scores = 0
    highest_pct = -1.0
    best_subject_name = "—"

    for sub in user_subjects:
        latest_score = all_scores.filter(subject=sub.name).first()
        if latest_score:
            pct = float(latest_score.percentage)
            total_percentage_sum += pct
            subjects_with_scores += 1
            if pct > highest_pct:
                highest_pct = pct
                best_subject_name = sub.name.upper()
        else:
            pct = 0
        subject_performances.append({"name": sub.name, "percent": pct})

    avg_percent = 0
    if subjects_with_scores > 0:
        avg_percent = round(total_percentage_sum / subjects_with_scores, 1)

    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()

    context = {
        "subjects": subject_performances,
        "best_subject": best_subject_name,
        "total_sessions": all_scores.count(), 
        "avg_percent": avg_percent,
        "profile": profile,
        "notif_count": unread_notifications,
        "dark_mode": settings_obj.dark_mode,
    }
    return render(request, "dashboard.html", context)
@login_required(login_url="login")
def edit_profile_view(request):
    profile = get_or_create_profile(request.user)
    
    if request.method == "POST":
        bio = request.POST.get("bio", "").strip()[:100]
        if bio:
            profile.bio = bio

        # Handling file uploads
        if 'profile_pic' in request.FILES:
            profile.profile_pic = request.FILES['profile_pic']
            
        if 'cover_pic' in request.FILES:
            profile.cover_pic = request.FILES['cover_pic']

        profile.save()
        messages.success(request, "Profile updated!")
        # Correctly passing the username to the 'profile' URL
        return redirect('profile', username=request.user.username)

    # Logic only reaches here if it's a GET request
    return render(request, "edit_profile.html", {"profile": profile})
def setup_subjects_view(request):
    if request.method == "POST":
        chosen = request.POST.getlist("subjects")

        if not chosen:
            return render(request, "setup_subjects.html", {
                "all_subjects": ALL_SUBJECTS,
                "error": "Please select at least 1 subject."
            })

        UserSubject.objects.filter(user=request.user).delete()
        UserSubject.objects.bulk_create([
            UserSubject(user=request.user, name=s) for s in chosen
        ])

        return redirect("dashboard")

    return render(request, "setup_subjects.html", {"all_subjects": ALL_SUBJECTS})


# ✅ ADD SCORE
from .forms import ScoreForm

@login_required
def add_score_view(request):
    if not request.user.subjects.exists():
        return redirect("setup_subjects")

    if request.method == "POST":
        form = ScoreForm(request.POST, user=request.user)
        if form.is_valid():
            score = form.save(commit=False)
            score.user = request.user
            score.save()
            return redirect("dashboard")
    else:
        form = ScoreForm(user=request.user)

    return render(request, "add_score.html", {"form": form})


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Score

@login_required
def view_scores_view(request):
    # 1. Fetch all scores for this user
    scores = Score.objects.filter(user=request.user).order_by("-created_at")

    # 2. Group scores by subject manually for the template
    grouped_scores = {}
    for s in scores:
        subject_name = s.subject # Assuming 'subject' is the field name in your Score model
        if subject_name not in grouped_scores:
            grouped_scores[subject_name] = []
        grouped_scores[subject_name].append(s)

    # 3. Create a list of subject names to trigger the "if subjects_sorted" check
    subjects_sorted = sorted(grouped_scores.keys())

    context = {
        "grouped_scores": grouped_scores,
        "subjects_sorted": subjects_sorted,
    }

    return render(request, "view_scores.html", context)


@login_required
def help_support_view(request):
    return render(request, "help_support.html")


# ✅ PROFILE VIEW + POSTS + FOLLOW SYSTEM
@login_required
def profile_view(request, username):
    user_obj = get_object_or_404(User, username=username)
    profile = get_or_create_profile(user_obj)

    posts = Post.objects.filter(user=user_obj).order_by("-created_at")

    followers_count = Follow.objects.filter(following=user_obj).count()
    following_count = Follow.objects.filter(follower=user_obj).count()

    is_following = False
    if request.user != user_obj:
        is_following = Follow.objects.filter(follower=request.user, following=user_obj).exists()

    context = {
        "user_obj": user_obj,
        "profile": profile,
        "posts": posts,
        "followers_count": followers_count,
        "following_count": following_count,
        "is_following": is_following,
    }
    return render(request, "profile.html", context)


# ✅ UPDATE PROFILE (BIO + PHOTOS)



# ✅ FOLLOW/UNFOLLOW
@login_required
def follow_toggle_view(request, username):
    target = get_object_or_404(User, username=username)

    if request.user == target:
        return redirect("profile", username=username)

    obj = Follow.objects.filter(follower=request.user, following=target)

    if obj.exists():
        obj.delete()
    else:
        Follow.objects.create(follower=request.user, following=target)

    return redirect("profile", username=username)


# ✅ CREATE POST
@login_required
def create_post_view(request):
    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if content:
            Post.objects.create(user=request.user, content=content)
    return redirect("profile", username=request.user.username)


# ✅ LIKE POST (AJAX)
@login_required
def like_post_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    existing = Like.objects.filter(user=request.user, post=post)
    if existing.exists():
        existing.delete()
        return JsonResponse({"status": "unliked", "likes": post.likes.count()})

    Like.objects.create(user=request.user, post=post)

    # ✅ notification
    if post.user != request.user:
        Notification.objects.create(
            user=post.user,
            message=f"{request.user.username} liked your post",
            link=f"/profile/{request.user.username}/"
        )

    return JsonResponse({"status": "liked", "likes": post.likes.count()})


# ✅ COMMENT POST (AJAX)
@login_required
def comment_post_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    text = request.POST.get("text", "").strip()

    if text:
        Comment.objects.create(user=request.user, post=post, text=text)

        # ✅ notification
        if post.user != request.user:
            Notification.objects.create(
                user=post.user,
                message=f"{request.user.username} commented on your post",
                link=f"/profile/{request.user.username}/"
            )

    return JsonResponse({"comments": post.comments.count()})


# ✅ NOTIFICATIONS PAGE
@login_required
def notifications_view(request):
    notes = Notification.objects.filter(user=request.user).order_by("-created_at")
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)

    return render(request, "notifications.html", {"notes": notes})

@login_required
def edit_post_view(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if post.user != request.user:
        return redirect("profile", username=post.user.username)

    if not post.can_edit():
        messages.error(request, "Edit time expired (10 minutes).")
        return redirect("profile", username=request.user.username)

    if request.method == "POST":
        new_content = request.POST.get("content", "").strip()
        if new_content:
            post.content = new_content
            post.save()
    return redirect("profile", username=request.user.username)

# core/views.py

def notifications_mark_read_view(request):
    # Your logic for marking notifications as read goes here
    pass

def clear_chat_view(request):
    # Your logic to clear the chat (e.g., deleting session data)
    request.session['chat_history'] = [] 
    return redirect('ai_chat_view') # or wherever you want them to go

from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

@login_required
def user_search(request):
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse({"results": []})

    users = (
        User.objects
        .filter(username__istartswith=q)
        .order_by("username")[:10]
    )

    return JsonResponse({"results": [u.username for u in users]})

from django.shortcuts import render, redirect
from .models import Score

from django.shortcuts import redirect
from .models import Score

from django.shortcuts import render, redirect
from .forms import ScoreForm  # Make sure you import your form class
from .models import Score

from django.shortcuts import render, redirect
from .forms import ScoreForm
from .models import Score

def add_score_view(request):
    if request.method == "POST":
        form = ScoreForm(request.POST, user=request.user)
        if form.is_valid():
            subject_data = form.cleaned_data['subject']

            if hasattr(subject_data, 'name'):
                subject_name = subject_data.name
            else:
                subject_name = str(subject_data)

            year = form.cleaned_data['year']
            correct = form.cleaned_data['correct']
            total = form.cleaned_data['total']

            Score.objects.update_or_create(
                user=request.user,
                subject=subject_name,
                year=year,
                defaults={
                    'correct': correct,
                    'total': total
                }
            )
            return redirect('dashboard')
    
    # --- MISSING PART BELOW ---
    else:
        # This handles the GET request when the user first opens the page
        form = ScoreForm(user=request.user)

    # This ensures an HttpResponse is ALWAYS returned.
    # It must be aligned with the first 'if' statement.
    return render(request, 'add_score.html', {'form': form})


import random
import string
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from .models import Wallet, Transaction


def _generate_receipt_code():
    # 15 characters, letters + digits (no symbols)
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(15))


def _unique_receipt_code():
    # make sure it doesn't exist already
    while True:
        code = _generate_receipt_code()
        if not WalletTransaction.objects.filter(code=code).exists():
            return code


@login_required
def wallet_set_pin_view(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    if request.method == "POST":
        pin1 = (request.POST.get("pin1") or "").strip()
        pin2 = (request.POST.get("pin2") or "").strip()

        if len(pin1) != 4 or not pin1.isdigit():
            messages.error(request, "PIN must be exactly 4 digits.")
            return redirect("wallet_set_pin")

        if pin1 != pin2:
            messages.error(request, "PINs do not match.")
            return redirect("wallet_set_pin")

        wallet.pin_hash = make_password(pin1)
        wallet.save()
        messages.success(request, "Wallet PIN set successfully.")
        return redirect("wallet")

    return render(request, "wallet_set_pin.html", {"wallet": wallet})


@login_required
def wallet_confirm_pin_view(request):
    wallet = get_object_or_404(Wallet, user=request.user)

    pending = request.session.get("pending_transfer")
    if not pending:
        messages.error(request, "No pending transfer found.")
        return redirect("wallet")

    if request.method == "POST":
        pin = (request.POST.get("pin") or "").strip()

        if len(pin) != 4 or not pin.isdigit():
            messages.error(request, "Enter a valid 4-digit PIN.")
            return redirect("wallet_confirm_pin")

        if not wallet.pin_hash or not check_password(pin, wallet.pin_hash):
            messages.error(request, "Incorrect PIN.")
            return redirect("wallet_confirm_pin")

        # Execute transfer atomically
        recipient = get_object_or_404(User, username__iexact=pending["to"])
        amount = Decimal(pending["amount"])
        remark = pending.get("remark", "")

        sender_wallet = wallet
        receiver_wallet, _ = Wallet.objects.get_or_create(user=recipient)

        if sender_wallet.balance < amount:
            messages.error(request, "Insufficient balance.")
            return redirect("wallet")

        with transaction.atomic():
            sender_wallet.balance -= amount
            receiver_wallet.balance += amount
            sender_wallet.save()
            receiver_wallet.save()

            code = _unique_receipt_code()
            tx = WalletTransaction.objects.create(
                code=code,
                sender=request.user,
                receiver=recipient,
                amount=amount,
                remark=remark,
                status="SUCCESS"
            )

        # Clear pending
        request.session.pop("pending_transfer", None)

        return redirect("wallet_receipt", code=tx.code)

    return render(request, "wallet_confirm_pin.html", {
        "wallet": wallet,
        "pending": pending,
    })


@login_required
def wallet_receipt_view(request, code):
    tx = get_object_or_404(WalletTransaction, code=code)
    return render(request, "wallet_receipt.html", {"tx": tx})


@login_required
def wallet_verify_view(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    result = None
    if request.method == "POST":
        code = (request.POST.get("code") or "").strip().upper()
        try:
            tx = WalletTransaction.objects.get(code=code)
            result = {"valid": True, "tx": tx}
        except WalletTransaction.DoesNotExist:
            result = {"valid": False, "tx": None}

    return render(request, "wallet_verify.html", {
        "wallet": wallet,
        "result": result,
    })

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.db import transaction as db_transaction
from decimal import Decimal
import secrets
import string

# USE THIS INSTEAD
from .models import Wallet, Transaction


def generate_tx_code():
    chars = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(15))


from django.db.models import Q # <--- Add this import at the top of views.py

@login_required
def wallet_home(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    # We filter transactions where the current user is EITHER the sender OR the receiver
    transactions = Transaction.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).order_by("-created_at")[:6]

    context = {
        "balance": wallet.balance,
        "transactions": transactions,
        "wallet": wallet, # Included in case your template needs the whole object
    }
    return render(request, "wallet.html", context)

@login_required
def wallet_send(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        amount_raw = request.POST.get("amount", "").strip()
        pin = request.POST.get("pin", "").strip()
        # Note: 'remark' is excluded because it's missing from your Transaction model

        # 1. Basic Validation
        if not username or not amount_raw or not pin:
            messages.error(request, "All fields are required.")
            return redirect("wallet_send")

        # 2. Verify Receiver
        try:
            receiver = User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect("wallet_send")

        if receiver == request.user:
            messages.error(request, "You cannot send money to yourself.")
            return redirect("wallet_send")

        # 3. Security Check (PIN)
        if not wallet.pin_hash:
            messages.error(request, "You must set your wallet PIN first.")
            return redirect("wallet_set_pin")

        if not check_password(pin, wallet.pin_hash):
            messages.error(request, "Incorrect PIN.")
            return redirect("wallet_send")

        # 4. Financial Validation
        try:
            amount = Decimal(amount_raw)
        except:
            messages.error(request, "Enter a valid amount.")
            return redirect("wallet_send")

        if amount <= 0:
            messages.error(request, "Amount must be greater than 0.")
            return redirect("wallet_send")

        if wallet.balance < amount:
            messages.error(request, "Insufficient balance.")
            return redirect("wallet_send")

        # 5. Execute Atomic Transaction
        receiver_wallet, _ = Wallet.objects.get_or_create(user=receiver)
        code = generate_tx_code()

        try:
           with db_transaction.atomic():
            # Deduct from sender (a)
            wallet.balance -= amount
            wallet.save()

            # Add to receiver (b)
            receiver_wallet.balance += amount  # <--- MUST BE +=
            receiver_wallet.save()

            # Create the Transaction Record
            Transaction.objects.create(
                sender=request.user,    # User A
                receiver=receiver,      # User B
                amount=amount,          # Store the absolute value (10.00)
                status="COMPLETED",
                code=code
            )
            messages.success(request, f"Successfully sent ${amount} to @{receiver.username}.")
            return redirect("wallet")
            
        except Exception as e:
            messages.error(request, f"Transfer failed: {str(e)}")
            return redirect("wallet_send")

    return render(request, "wallet_send.html", {"balance": wallet.balance})
@login_required
def wallet_betting(request):
    return render(request, "wallet_betting.html")


@login_required
def wallet_verify(request):
    verified = None
    tx_obj = None

    if request.method == "POST":
        code = request.POST.get("code", "").strip().upper()

        if not code:
            verified = False
        else:
            tx_obj = Transaction.objects.filter(code=code).first()
            verified = True if tx_obj else False

    return render(request, "wallet_verify.html", {"verified": verified, "tx": tx_obj})


from django.db.models import Q # Make sure this is imported at the top of the file

@login_required
def wallet_history(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    
    # Check if the user is the sender OR the receiver
    transactions = Transaction.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).order_by("-created_at")

    return render(request, "wallet_history.html", {
        "balance": wallet.balance, 
        "transactions": transactions
    })

from django.http import JsonResponse
from django.contrib.auth.models import User

def user_search(request):
    query = request.GET.get('q', '').strip()
    if len(query) < 1:
        return JsonResponse({'results': []})
    
    # Exclude the current user so they don't send money to themselves
    users = User.objects.filter(
        username__icontains=query
    ).exclude(id=request.user.id)[:5] 
    
    results = [user.username for user in users]
    return JsonResponse({'results': results})

from django.http import JsonResponse
from .models import CoinFlipBet

def flip_coin(request):
    if request.method == "POST":
        amount = float(request.POST.get('amount'))
        choice = request.POST.get('choice') # 'HEADS' or 'TAILS'
        profile = request.user.profile
        
        # 1. Validation
        if profile.balance < amount:
            return JsonResponse({'error': 'Insufficient funds'}, status=400)
            
        # 2. Logic
        import random
        result = random.choice(['HEADS', 'TAILS'])
        win = (choice == result)
        
        if win:
            # Add the profit (Win 2000 means +1000 net or 2000 total back)
            profile.balance += amount  # If they bet 1000 and win 2000 total
        else:
            profile.balance -= amount
            
        profile.save() # THIS IS CRITICAL - Updates the DB
        
        return JsonResponse({
            'result': result,
            'win': win,
            'new_balance': float(profile.balance) # Send new balance back to JS
        })
    
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q, Max
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import Conversation, Message

User = get_user_model()


from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import Conversation, Message

User = get_user_model()


def _status_for(user_obj):
    """
    Returns: (is_online: bool, text: str)
    """
    try:
        last = user_obj.userprofile.last_seen
    except Exception:
        return (False, "Offline")

    now = timezone.now()
    diff = (now - last).total_seconds()

    # consider online if seen within 120 seconds
    if diff <= 120:
        return (True, "Online")

    mins = int(diff // 60)
    if mins < 60:
        return (False, f"Active {mins} minute{'s' if mins != 1 else ''} ago")

    hours = int(mins // 60)
    return (False, f"Active {hours} hour{'s' if hours != 1 else ''} ago")


@login_required
def messages_inbox(request):
    me = request.user
    convs = Conversation.objects.filter(Q(user1=me) | Q(user2=me)).order_by("-updated_at")

    cards = []
    for c in convs:
        other = c.other_user(me)
        last_msg = c.messages.last()

        # Logic for unread count
        if c.user1_id == me.id:
            unread = c.messages.filter(read_by_user1=False).exclude(sender=me).count()
        else:
            unread = c.messages.filter(read_by_user2=False).exclude(sender=me).count()

        # GET ONLINE STATUS USING YOUR HELPER
        is_online, status_text = _status_for(other)

        cards.append({
            "id": c.id,
            "other": other,
            "is_online": is_online,      # Added this
            "status_text": status_text,  # Added this
            "last_text": (last_msg.text[:70] + "…") if last_msg and len(last_msg.text) > 70 else (last_msg.text if last_msg else "Start a conversation…"),
            "last_time": last_msg.created_at if last_msg else c.created_at,
            "unread": unread,
        })

    return render(request, "messages.html", {"conversations": cards})


@login_required
def user_search_ajax(request):
    """
    Autocomplete: /messages/search/?q=ja
    returns usernames + dp urls
    """
    me = request.user
    q = (request.GET.get("q") or "").strip()
    if not q:
        return JsonResponse({"ok": True, "results": []})

    # Search for usernames starting with 'q'
    users = User.objects.filter(username__istartswith=q).exclude(id=me.id)[:8]
    
    results = []
    for u in users:
        dp_url = ""
        try:
            # Check if userprofile and profile_pic exist
            if hasattr(u, 'userprofile') and u.userprofile.profile_pic:
                dp_url = u.userprofile.profile_pic.url
        except Exception:
            dp_url = ""
            
        results.append({
            "username": u.username,
            "dp": dp_url, # Key is 'dp' to match the JS template literal
        })
        
    return JsonResponse({"ok": True, "results": results})


from django.db.models import Q

from django.shortcuts import redirect, get_object_or_404
from django.db.models import Q
from .models import Conversation

@login_required
def start_chat(request, username):
    other_user = get_object_or_404(User, username=username)
    
    # Prevent chatting with yourself
    if other_user == request.user:
        return redirect('messages_inbox')

    # 1. Look for existing conversation (check both slots)
    conv = Conversation.objects.filter(
        (Q(user1=request.user) & Q(user2=other_user)) |
        (Q(user1=other_user) & Q(user2=request.user))
    ).first()

    # 2. If it doesn't exist, create it
    if not conv:
        conv = Conversation.objects.create(user1=request.user, user2=other_user)
        # Force save to ensure ID exists
        conv.save()

    # 3. REDIRECT to the actual thread
    return redirect('chat_thread', conv_id=conv.id)
@login_required
def chat_thread(request, conv_id):
    me = request.user
    # Use select_related to make sure user objects are loaded
    conv = get_object_or_404(Conversation.objects.select_related('user1', 'user2'), id=conv_id)

    # Compare the objects directly - this is more reliable in Django
    if me != conv.user1 and me != conv.user2:
        print(f"DEBUG: Access denied for {me}. Conv users: {conv.user1}, {conv.user2}") # Check your console!
        return redirect("messages_inbox")

    other = conv.other_user(me)

    # --- Mark as Read Logic ---
    # Optimized: update all at once
    unread_msgs = conv.messages.exclude(sender=me)
    if conv.user1 == me:
        unread_msgs.filter(read_by_user1=False).update(read_by_user1=True)
    else:
        unread_msgs.filter(read_by_user2=False).update(read_by_user2=True)

    msgs = conv.messages.select_related("sender").all()
    is_online, status_text = _status_for(other)

    return render(request, "chat.html", {
        "conv": conv,
        "other": other,
        "messages": msgs,
        "is_online": is_online,
        "status_text": status_text,
    })


from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required

@login_required
def chat_send_ajax(request, conv_id):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST only"}, status=400)

    me = request.user
    conv = get_object_or_404(Conversation, id=conv_id)

    # 1. Get all possible inputs
    text = (request.POST.get("text") or "").strip()
    image = request.FILES.get("image")
    audio = request.FILES.get("audio") # <--- Make sure you are grabbing this!

    # 2. Update the logic check: Message is only "empty" if ALL THREE are missing
    if not text and not image and not audio:
        return JsonResponse({"ok": False, "error": "Message cannot be empty"}, status=400)

    # 3. Create the message
    msg = Message.objects.create(
        conversation=conv,
        sender=me,
        text=text,
        image=image,
        audio=audio, # <--- Save it here
        read_by_user1=(conv.user1_id == me.id),
        read_by_user2=(conv.user2_id == me.id),
    )
    
    # ... rest of your view (save conv timestamp and return JsonResponse)
@login_required
def chat_poll_ajax(request, conv_id):
    me = request.user
    conv = get_object_or_404(Conversation, id=conv_id)

    if not (conv.user1_id == me.id or conv.user2_id == me.id):
        return JsonResponse({"ok": False, "error": "Not allowed"}, status=403)

    after_str = request.GET.get("after", "0")
    try:
        after = int(after_str)
    except ValueError:
        after = 0

    qs = conv.messages.select_related("sender").filter(id__gt=after).order_by("id")

    messages_data = []
    new_message_ids = []  # Collect IDs of messages we're about to mark as read

    for m in qs:
        item = {
            "id": m.id,
            "mine": (m.sender_id == me.id),
            "text": m.text or "",           # avoid null → ""
            "time": m.created_at.strftime("%I:%M %p").lstrip("0"),
            "sender": m.sender.username,
            "image_url": m.image.url if m.image else None,
            "audio_url": m.audio.url if m.audio else None,
        }
        messages_data.append(item)

        # Only mark incoming messages that are actually being delivered now
        if m.sender_id != me.id:
            new_message_ids.append(m.id)

    # Mark only the newly delivered incoming messages as read
    if new_message_ids:
        incoming_new = conv.messages.filter(id__in=new_message_ids)
        if conv.user1_id == me.id:
            incoming_new.filter(read_by_user1=False).update(read_by_user1=True)
        else:
            incoming_new.filter(read_by_user2=False).update(read_by_user2=True)

    return JsonResponse({
        "ok": True,
        "messages": messages_data,
    })
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse

User = get_user_model()

@login_required
def wallet_user_search(request):
    q = (request.GET.get("q") or "").strip()
    if not q:
        return JsonResponse({"ok": True, "results": []})

    users = User.objects.filter(username__istartswith=q).exclude(id=request.user.id)[:8]

    results = [{"username": u.username} for u in users]
    return JsonResponse({"ok": True, "results": results})

import json
from collections import defaultdict
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Score, UserSubject

import json
from collections import defaultdict
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Score, UserSubject

@login_required
def graph_view(request):
    user_subjects = list(
        UserSubject.objects.filter(user=request.user).values_list("name", flat=True)
    )

    scores = (
        Score.objects.filter(user=request.user, subject__in=user_subjects)
        .order_by("year", "created_at")
    )

    # labels will be years: ["2020","2021","2022"...]
    labels = sorted({str(s.year) for s in scores})

    # subject -> year -> percentage
    subject_year_pct = defaultdict(dict)
    for s in scores:
        subject_year_pct[s.subject][str(s.year)] = float(s.percentage)

    datasets = []
    for subj in user_subjects:
        data = [subject_year_pct.get(subj, {}).get(y, None) for y in labels]
        datasets.append({
            "label": subj,
            "data": data,
        })

    context = {
        "labels_json": json.dumps(labels),
        "datasets_json": json.dumps(datasets),
        "subjects": user_subjects,
    }
    return render(request, "graph.html", context)

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.shortcuts import render, redirect
from django.contrib.auth.models import User

from .models import UserSettings


def get_or_create_settings(user):
    settings_obj, _ = UserSettings.objects.get_or_create(user=user)
    return settings_obj


@login_required
def settings_view(request):
    # Use the related_name="settings" we defined in the model
    s, _ = UserSettings.objects.get_or_create(user=request.user)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "toggle_dark_mode":
            s.dark_mode = not s.dark_mode
            s.save()
            return redirect("settings")

        elif action == "update_notifications":
            s.notify_likes = bool(request.POST.get("notify_likes"))
            s.notify_comments = bool(request.POST.get("notify_comments"))
            s.notify_follows = bool(request.POST.get("notify_follows"))
            s.save()
            messages.success(request, "Notification settings updated.")
            return redirect("settings")

    # Send 'dark_mode' specifically so the <body> class works
    return render(request, "settings.html", {
        "s": s, 
        "dark_mode": s.dark_mode
    })


@login_required
def delete_account_view(request):
    """
    Secure delete:
    - requires password
    - requires typing DELETE
    """
    if request.method == "POST":
        password = request.POST.get("password", "")
        confirm_text = request.POST.get("confirm_text", "").strip().upper()

        if confirm_text != "DELETE":
            messages.error(request, "Type DELETE to confirm account deletion.")
            return redirect("settings")

        if not check_password(password, request.user.password):
            messages.error(request, "Incorrect password.")
            return redirect("settings")

        # delete account
        user = request.user
        logout(request)
        user.delete()

        messages.success(request, "Your account has been deleted.")
        return redirect("login")

    return redirect("settings")

import json
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder

from .models import UserProfile, Post, Comment, Like, Follow, Score, UserSettings


@login_required
def export_data_view(request):
    u = request.user

    profile = UserProfile.objects.filter(user=u).values(
        "bio", "created_at"
    ).first()

    settings = UserSettings.objects.filter(user=u).values().first()

    posts = list(Post.objects.filter(user=u).values("id", "content", "created_at"))
    comments = list(Comment.objects.filter(user=u).values("id", "post_id", "text", "created_at"))
    likes = list(Like.objects.filter(user=u).values("id", "post_id", "created_at"))
    follows = list(Follow.objects.filter(follower=u).values("following_id", "created_at"))

    scores = list(Score.objects.filter(user=u).values(
        "id", "subject", "score", "total", "created_at"
    ))

    tx = list(WalletTransaction.objects.filter(user=u).values(
        "ref_code", "amount", "direction", "remark", "created_at"
    ))

    payload = {
        "user": {"username": u.username, "date_joined": u.date_joined},
        "profile": profile,
        "settings": settings,
        "posts": posts,
        "comments": comments,
        "likes": likes,
        "follows": follows,
        "scores": scores,
        "wallet_transactions": tx,
    }

    data = json.dumps(payload, cls=DjangoJSONEncoder, indent=2)

    resp = HttpResponse(data, content_type="application/json")
    resp["Content-Disposition"] = f'attachment; filename="gradify_{u.username}_data.json"'
    return resp

from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

@require_POST
@login_required
def deactivate_account_view(request):
    user = request.user
    user.is_active = False
    user.save(update_fields=["is_active"])
    logout(request)
    return redirect("login")

# core/signals.py
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils import timezone
from .models import UserProfile

@receiver(user_logged_in)
def update_streak(sender, request, user, **kwargs):
    # Use get_or_create to ensure the profile exists
    profile, created = UserProfile.objects.get_or_create(user=user)
    today = timezone.now().date()

    if profile.last_login_date:
        # Check if they logged in yesterday to increment streak
        yesterday = today - timezone.timedelta(days=1)
        if profile.last_login_date == yesterday:
            profile.streak_count += 1
        elif profile.last_login_date < yesterday:
            profile.streak_count = 1  # Reset if they missed a day
    else:
        profile.streak_count = 1  # First time login

    profile.last_login_date = today
    profile.save()