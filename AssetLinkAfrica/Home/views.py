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
  
