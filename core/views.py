from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.shortcuts import render, redirect
from .models import UserSubject, Score

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

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

            # ✅ redirect after successful login
            return redirect("dashboard")

        messages.error(request, "Invalid username or password.")
        return redirect("login")

    return render(request, "login.html")

@login_required
@login_required
def dashboard_view(request):
    user_subjects = UserSubject.objects.filter(user=request.user)
    if not user_subjects.exists():
        return redirect("setup_subjects")

    all_scores = Score.objects.filter(user=request.user)
    subject_performances = []
    highest_pct = -1.0
    best_subject_name = "—"

    for sub in user_subjects:
        latest_score = all_scores.filter(subject=sub.name).first()
        
        # ✅ FIXED: Removed () because percentage is now a @property
        pct = latest_score.percentage if latest_score else 0
        
        subject_performances.append({
            'name': sub.name,
            'percent': pct
        })
        
        if latest_score and pct > highest_pct:
            highest_pct = pct
            best_subject_name = sub.name.upper()

    avg_percent = 0
    if all_scores.exists():
        # ✅ FIXED: Also removed () here if it was present
        avg_percent = round(sum(s.percentage for s in all_scores) / all_scores.count(), 1)

    context = {
        "subjects": subject_performances,
        "best_subject": best_subject_name,
        "streak_days": get_streak(request.user),
        "total_sessions": all_scores.count(),
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
@login_required
def add_score_view(request):
    if not request.user.subjects.exists():
        return redirect("setup_subjects")

    if request.method == "POST":
        # Passing 'user' here is CRITICAL
        form = ScoreForm(request.POST, user=request.user)
        if form.is_valid():
            score = form.save(commit=False)
            score.user = request.user
            score.save()
            return redirect("dashboard")
    else:
        # Passing 'user' here makes the dropdown show your subjects on page load
        form = ScoreForm(user=request.user)

    return render(request, "add_score.html", {"form": form})
@login_required
def view_scores_view(request):
    scores = Score.objects.filter(user=request.user)
    return render(request, "view_scores.html", {"scores": scores})


@login_required
def help_support_view(request):
    return render(request, "help_support.html")

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