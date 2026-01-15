"""
URL configuration for gradify project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView   # ← Important import!
from core import views # Replace 'my_app_name' with your actual app name

urlpatterns = [
    # Redirect root (/) → register page (using the named URL)
    path('', RedirectView.as_view(pattern_name='register', permanent=False)),

    path('admin/', admin.site.urls),

    # Include your core app URLs (this makes /register/, /login/, etc. work)
    path('', include('core.urls')),  # ← '' means no prefix — all core paths at root level
]
