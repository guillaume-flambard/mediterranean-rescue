"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
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
from django.urls import path

# Les adresses de tout le site. Pour l'instant, seulement l'admin : /admin/
# Une application qui a ses propres adresses les garde dans son urls.py, branché ici avec
# include() (tutoriel, partie 1 : https://docs.djangoproject.com/fr/6.1/intro/tutorial01/).
urlpatterns = [
    path("admin/", admin.site.urls),
]
