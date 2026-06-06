from django.urls import path

from web.views import api_recommend, home


urlpatterns = [
    path("", home, name="home"),
    path("api/recommend/", api_recommend, name="api_recommend"),
]
