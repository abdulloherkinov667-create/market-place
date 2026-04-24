from unicodedata import name
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render, redirect, get_list_or_404
from django.contrib import messages
from django.db.models import Q
from .models import UzumProduct, ShopingModel, Users, Order, OrderItem, Like, User_carts
from django.core.paginator import Paginator
from django.views.generic import (
    ListView, TemplateView, DetailView
)

from django.shortcuts import render
import requests
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout




def update_order_status(request, order_id, new_status):
    order = get_object_or_404(Order, id=order_id)
    valid_statuses = [choice[0] for choice in Order.OrderStatusChoice.choices]
    
    if new_status in valid_statuses:
        order.is_status = new_status
        order.save()
        messages.success(request, f"Buyurtma holati '{new_status}'ga o'zgartirildi.")
    else:
        messages.error(request, "Xato: Bunday status mavjud emas!")
        
    return redirect(request.META.get('HTTP_REFERER', '/'))


#userlarni htmlga chiqarish uchun viuw
def customers(request):
    users = Users.objects.filter(user_type='Clent') 
    return render(request, 'customers.html', {'users': users})


#yangi manzil qoshish html uchun viuw
def add_address(request):
    return render(request, 'userlar/add_address.html')