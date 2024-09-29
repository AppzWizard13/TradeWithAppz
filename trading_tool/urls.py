from . import views
from django.urls import path
from django.contrib.auth import views as auth_views
from trading_tool.views import DashboardView


urlpatterns = [
    path('dashboard', views.DashboardView.as_view(), name='dashboard'),

]