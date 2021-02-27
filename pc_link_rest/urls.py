from django.contrib import admin
from django.urls import path, include, re_path
from accounts import views as account_views
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('pc_calculator.urls')),
    path('accounts/', include('accounts.urls')),
    re_path(r'^maintenance-mode/', include('maintenance_mode.urls')),
]

if settings.DEBUG == True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
