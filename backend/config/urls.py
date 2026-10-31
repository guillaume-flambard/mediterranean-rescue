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
from django.urls import include, path

# Les adresses de tout le site. Chaque application garde les siennes dans son propre
# urls.py, branché ici avec include() (tutoriel, partie 1).
urlpatterns = [
    # L'API lue par la carte : /api/operations/ (voir operations/urls.py).
    path("api/operations/", include("operations.urls")),
    # L'admin, pour relire et publier : /admin/
    path("admin/", admin.site.urls),
]
