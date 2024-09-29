from . import views
from django.urls import path
from django.contrib.auth import views as auth_views
from account.views import UserRegistrationView


urlpatterns = [
    # landing page
    # path('', views.homePage, name = 'home'),
    # # login 
    # path('login', views.UserloginView.as_view(), name = 'login'),
    # path('logout', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    # path('logout', views.UserRegistrationView.as_view(), name='user_registration'),
    # # path('dashboard', views.dashboard, name='dashboard'),
    # path('dashboard', views.DashboardView.as_view(), name='dashboard'),
    # # path('explore_more', views.ExpoloreMore, name='explore_more'),
    

    
    # # path('logout', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

   


      

]