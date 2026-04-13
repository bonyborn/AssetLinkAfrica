from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.login, name='login'),
    path('listing/', views.listings, name='listing'),
    path('post_listings/', views.post_listings, name='post_listings'),
    path('details/', views.details, name='details'),
    path('details/', views.dashboard, name='details'), 
    path('admin/', views.admin, name='admin'), 
    path('transactions/', views.transactions, name="transactions"),
    path('settings/', views.settings, name='settings')
]
