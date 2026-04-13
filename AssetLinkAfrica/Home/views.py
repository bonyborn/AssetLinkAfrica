from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request, 'index.html')
  
def admin(request):
    return render(request, 'admin.html')

def dashboard(request):
    return render(request, 'dashboard.html')

def transactions(request):
    return render(request, 'transactions.html')

def listings(request):
    return render(request, 'listings.html')
    
def post_listings(request):
    return render(request, 'post_listings.html')

def details(request):
    return render(request, 'details.html')

def settings(request):
    return render(request, 'settings.html')

def signup(request):
    return render(request, 'signup.html')

def login(request):
    return render(request, 'login.html')
    
