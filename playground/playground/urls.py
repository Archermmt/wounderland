"""playground URL Configuration

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

from django.contrib import admin
from django.urls import path
from django.conf.urls import url
from game import views as game_views

urlpatterns = [
    path("admin/", admin.site.urls),
    url("village", game_views.village),
    url("start_game", game_views.start_game, name="start_game"),
    url("agent_think", game_views.agent_think, name="agent_think"),
    url("agent_save", game_views.agent_save, name="agent_save"),
    url("get_time", game_views.get_time, name="get_time"),
    url("user_login", game_views.user_login, name="user_login"),
    url("user_logout", game_views.user_logout, name="user_logout"),
    url("user_add_key", game_views.user_add_key, name="user_add_key"),
]
