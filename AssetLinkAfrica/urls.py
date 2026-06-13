from django.contrib import admin
from django.urls import path
from django.urls import include

from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [

    path('admin/', admin.site.urls),

    path('', include('core.urls')),

    # user auth routes (register/login/logout)
    path('', include('users.urls')),

    path(
        'listings/',
        include('listings.urls')
    ),

    path(
        'bookings/',
        include('bookings.urls')
    ),

    path(
        'payments/',
        include('payments.urls')
    ),

    path(
        'dashboard/',
        include('dashboard.urls')
    ),

]

urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)
