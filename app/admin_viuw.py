from unicodedata import name

from django.shortcuts import render, redirect, get_list_or_404
from django.contrib import messages
from .models import UzumProduct, ShopingModel, Users, Order, OrderItem
from django.core.paginator import Paginator
from django.views.generic import (
    ListView, TemplateView, DetailView
)

from django.shortcuts import render
import requests
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout


def admin_home(request):
    return render(request, 'admin/admin_home.html')


#admin buyurtmalarni korsatish uchun
def buyurtma_admin(request):
    order = Order.objects.all().order_by('created_at')
    return render(request, 'admin/buyurtma.html', {'orders': order})


#admin buyurtmalar tarixi html 
def buyurma_details(request, pk):
    order = Order.objects.get(id=pk)
    order_details = OrderItem.objects.filter(order=order)
    return render(request, 'admin/buyutma_a_de.html', {'order': order, 'order_details': order_details})


#mijozlar html
def clent_html(request):
    return render(request, 'admin/mijozlar.html')


#kassa html
def kassa_html(request):
    return render(request, 'admin/kassa.html')


#hisobot html
def hisobothtml(request):
    return render(request, 'admin/hisobot.html')