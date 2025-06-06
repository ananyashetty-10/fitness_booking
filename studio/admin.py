from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import FitnessClass

@admin.register(FitnessClass)
class FitnessClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'instructor', 'datetime', 'available_slots')
    list_filter = ('instructor', 'datetime')
    search_fields = ('name', 'instructor')

