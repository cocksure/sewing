from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include

from config.veiws import dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", dashboard, name="dashboard"),
    path("info/", include("info.urls")),
    path("core/", include("core.urls")),
    path("sewing/", include("sewing.urls")),

    # Аутентификация
    path("login/", auth_views.LoginView.as_view(template_name="auth/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),
    path("select2/", include("django_select2.urls")),
]

# handler403 = "core.errors.handler403"
# handler404 = "core.errors.handler404"
# handler500 = "core.errors.handler500"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
