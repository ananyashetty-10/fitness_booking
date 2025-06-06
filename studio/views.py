from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from io import BytesIO
import json

from django.shortcuts import render, redirect
from django.utils.dateparse import parse_datetime
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from .models import FitnessClass, Booking
from .serializers import FitnessClassSerializer, BookingSerializer


# Main page view
def main_page(request):
    return render(request, 'main_page.html')


# Dashboard view (requires login)
@login_required
def dashboard_view(request):
    return render(request, 'dashboard.html', {'user': request.user})


# Logout view
def user_logout(request):
    logout(request)
    return redirect('user_login')


# Custom admin_required decorator
def admin_required(view_func):
    return login_required(user_passes_test(lambda u: u.is_staff)(view_func))


# API to create a fitness class (admin only)
@admin_required
@api_view(['POST'])
def create_class(request):
    data = request.data
    name = data.get('name')
    instructor = data.get('instructor')
    datetime_str = data.get('datetime')
    available_slots = data.get('available_slots')

    if not all([name, instructor, datetime_str, available_slots]):
        return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        datetime_obj = parse_datetime(datetime_str)
        if not datetime_obj:
            raise ValueError("Invalid datetime format")

        fitness_class = FitnessClass.objects.create(
            name=name,
            instructor=instructor,
            datetime=datetime_obj,
            available_slots=int(available_slots)
        )
        return Response({"success": True, "class_id": fitness_class.id}, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Show all classes (no authentication required)
@api_view(['GET'])
def get_classes(request):
    classes = FitnessClass.objects.all()

    if request.accepted_renderer.format == 'json':
        serializer = FitnessClassSerializer(classes, many=True)
        return Response(serializer.data)

    context = {'classes': classes}
    return render(request, 'classes.html', context)


# Book a class (no authentication required)
@api_view(['GET', 'POST'])
def book_class(request):
    if request.method == 'GET':
        classes = FitnessClass.objects.filter(available_slots__gt=0)
        return render(request, 'book_class.html', {'classes': classes})

    data = request.data
    context = {}

    try:
        fitness_class = FitnessClass.objects.get(id=data.get('class_id'))
    except FitnessClass.DoesNotExist:
        context['error'] = "Class not found"
        return render(request, 'book_class.html', context)

    if fitness_class.available_slots <= 0:
        context['error'] = "Class is full"
        return render(request, 'book_class.html', context)

    client_name = data.get('client_name')
    client_email = data.get('client_email')

    if not client_name or not client_email:
        context['error'] = "Please provide your name and email"
        return render(request, 'book_class.html', context)

    Booking.objects.create(
        fitness_class=fitness_class,
        client_name=client_name,
        client_email=client_email
    )
    fitness_class.available_slots -= 1
    fitness_class.save()

    context['success'] = "Booking successful!"
    context['classes'] = FitnessClass.objects.filter(available_slots__gt=0)
    return render(request, 'book_class.html', context)


# View bookings by email (no authentication required)
@api_view(['GET', 'POST'])
def get_bookings(request):
    if request.method == 'GET' and 'email' not in request.GET:
        return render(request, 'get_bookings.html')

    email = request.GET.get('email') or request.POST.get('email')
    context = {'email': email}

    if not email:
        context['error'] = "Email required"
        return render(request, 'get_bookings.html', context)

    bookings = Booking.objects.filter(client_email=email)

    if not bookings.exists():
        context['message'] = "No bookings found for this email."
        return render(request, 'get_bookings.html', context)

    context['bookings'] = bookings
    return render(request, 'get_bookings.html', context)


# User login view
@api_view(['GET', 'POST'])
def user_login(request):
    if request.method == 'GET':
        return render(request, 'login.html')

    email = request.POST.get('email')
    password = request.POST.get('password')
    context = {'email': email}

    if not email or not password:
        context['error'] = "Email and password required"
        return render(request, 'login.html', context)

    User = get_user_model()
    try:
        user_obj = User.objects.get(email=email)
        user = authenticate(username=user_obj.username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('dashboard')
        else:
            context['error'] = "Invalid credentials"
            return render(request, 'login.html', context)
    except User.DoesNotExist:
        context['error'] = "User not found"
        return render(request, 'login.html', context)


# User signup view
from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_protect  # not strictly needed, but explicit
from django.contrib.auth.models import User

@csrf_protect
def user_signup(request):
    if request.method == 'GET':
        return render(request, 'signup.html')

    username = request.POST.get('username')
    email = request.POST.get('email')
    password = request.POST.get('password')

    context = {
        'username': username or '',
        'email': email or ''
    }

    if not username or not email or not password:
        context['error'] = "All fields are required."
        return render(request, 'signup.html', context)

    User = get_user_model()
    if User.objects.filter(username=username).exists():
        context['error'] = "Username already exists."
        return render(request, 'signup.html', context)

    if User.objects.filter(email=email).exists():
        context['error'] = "Email already exists."
        return render(request, 'signup.html', context)

    user = User.objects.create_user(username=username, email=email, password=password)
    context['success'] = f"User {user.username} registered successfully!"
    context['username'] = ''
    context['email'] = ''
    return render(request, 'signup.html', context)
