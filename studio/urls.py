from django.urls import path
from django.http import JsonResponse

from .views import create_class, get_classes, book_class, get_bookings, user_login, user_signup  # Import user_login and user_signup
from .views import main_page  
from . import views


urlpatterns = [
   
    path('classes/', get_classes, name='get_classes'),
    path('book/', book_class, name='book_class'),
    path('bookings/', get_bookings, name='get_bookings'),
    path('create-class/', create_class, name='create_class'),
    path('login/', user_login, name='user_login'),  # Add login path
    path('signup/', user_signup, name='user_signup'),  # Add signup path
  path('', main_page, name='main_page'),
  path('dashboard/', views.dashboard_view, name='dashboard'),
  path('logout/', views.user_logout, name='logout'),


]
