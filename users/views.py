from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render

from .forms import RegisterForm
from .models import User


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully.")
            return redirect("dashboard")
        messages.error(request, "Please fix the errors below.")
    else:
        form = RegisterForm()
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        identifier = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = None

        if identifier and password:
            if "@" in identifier:
                email_user = User.objects.filter(email__iexact=identifier).first()
                if email_user:
                    user = authenticate(
                        request,
                        username=email_user.username,
                        password=password,
                    )
            if not user:
                user = authenticate(request, username=identifier, password=password)

        next_page = request.POST.get("next") or request.GET.get("next")

        if user:
            login(request, user)
            return redirect(next_page or "dashboard")

        messages.error(request, "Invalid username or password.")

    return render(request, "users/login.html")


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("home")
