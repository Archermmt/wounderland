"""environment URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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

from django.conf.urls import url
from django.contrib import admin
from django.urls import path
from world import views as world_views

urlpatterns = [
    path("admin/", admin.site.urls),
    url("village", world_views.village),
    url("start_game", world_views.start_game, name="start_game"),
    url("agent_think", world_views.agent_think, name="agent_think"),
    url("user_login", world_views.user_login, name="user_login"),
    url("user_logout", world_views.user_logout, name="user_logout"),
    url("user_add_key", world_views.user_add_key, name="user_add_key"),
]
