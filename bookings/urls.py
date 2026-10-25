from django.urls import path
from . import views


urlpatterns = [

    path(
        '',
        views.my_bookings,
        name='bookings'
    ),

    path(
        'create/<int:id>/',
        views.create_booking,
        name='create_booking'
    ),

]
