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
