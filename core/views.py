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

@login_required
def dashboard_view(request):
    user_subjects = UserSubject.objects.filter(user=request.user)
    if not user_subjects.exists():
        return redirect("setup_subjects")

    subject_performances = []
    scored_pcts = []          # only subjects that actually have a score
    highest_pct = -1.0
    best_subject_name = "—"

    for sub in user_subjects:
        # ✅ explicit "latest" score for THIS subject
        latest_score = (
            Score.objects
            .filter(user=request.user, subject=sub.name)
            .order_by("-created_at")
            .first()
        )

        pct = latest_score.percentage if latest_score else 0

        subject_performances.append({
            "name": sub.name,
            "percent": pct,
        })

        # Only count subjects that have at least one saved score
        if latest_score:
            scored_pcts.append(pct)

            # ✅ best subject based on latest per subject
            if pct > highest_pct:
                highest_pct = pct
                best_subject_name = sub.name  # keep natural casing

    # ✅ average = average of "latest per subject" percentages (not every score ever)
    avg_percent = round(sum(scored_pcts) / len(scored_pcts), 1) if scored_pcts else 0

    # ✅ sessions = number of saved score entries (so 2 saved scores = 2 sessions)
    total_sessions = Score.objects.filter(user=request.user).count()

    context = {
        "subjects": subject_performances,
        "best_subject": best_subject_name,
        "streak_days": get_streak(request.user),
        "total_sessions": total_sessions,
        "avg_percent": avg_percent,
    }
    return render(request, "dashboard.html", context)


ALL_SUBJECTS = [
    "English", "Mathematics", "Physics", "Chemistry",
    "Biology", "Government", "Economics", "Literature",
    "Geography", "History", "Commerce", "Accounting",
    "Civic Education", "Agricultural Science", "CRS", "IRS",
    "Further Mathematics",
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
