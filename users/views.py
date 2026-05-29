from django.contrib import messages
from django.shortcuts import render
from django.shortcuts import redirect

from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth import authenticate

from .forms import RegisterForm


def register_view(request):

    if request.method == 'POST':

        form = RegisterForm(request.POST)

        if form.is_valid():

            user = form.save()

            login(request, user)

            messages.success(request, 'Account created successfully.')

            return redirect('home')

        messages.error(request, 'Please fix the errors below.')

    else:

        form = RegisterForm()

    return render(
        request,
        'users/register.html',
        {'form': form}
    )


def login_view(request):

    if request.method == 'POST':

        username = request.POST.get('username')

        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user:

            login(request, user)

            return redirect('dashboard')

        messages.error(request, 'Invalid username or password.')

    return render(
        request,
        'users/login.html'
    )


def logout_view(request):

    logout(request)

    messages.success(request, 'You have been logged out.')

    return redirect('home')
