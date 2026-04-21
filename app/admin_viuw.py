from unicodedata import name

from django.http import JsonResponse
from django.shortcuts import render, redirect, get_list_or_404
from django.contrib import messages
from app.models import UzumProduct, ShopingModel, Users, Order, OrderItem
from django.core.paginator import Paginator
from django.utils.timezone import localdate
from django.db.models import Sum, F, ExpressionWrapper, BigIntegerField, Q, Count, Case, When, IntegerField
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


#bugungi tushum uchun alohida viuw
def get_today_income_context():
    today = localdate()
    orders = Order.objects.filter(created_at__date=today).order_by('-created_at')
    today_income = OrderItem.objects.filter(order__created_at__date=today).aggregate(
        total=Sum(ExpressionWrapper(F('price') * F('count'), output_field=BigIntegerField()))
    )['total'] or 0
    sales_count = orders.count()
    return {
        'today_income': today_income,
        'sales_count': sales_count,
        'growth_percent': 0,
        'orders': orders,
    }


#bugungi tushum uchun alohida viuw
def today_income(request):
    context = get_today_income_context()
    return render(request, 'admin/buyurtma.html', context)


#admin buyurtmalarni korsatish uchun
def buyurtma_admin(request):
    context = get_today_income_context()
    return render(request, 'admin/buyurtma.html', context)


#admin buyurtmalar tarixi html 
def buyurma_details(request, pk):
    order = Order.objects.get(id=pk)
    order_details = OrderItem.objects.filter(order=order)
    return render(request, 'admin/buyutma_a_de.html', {'order': order, 'order_details': order_details})
    

#mijozlar html va for chiqazish uchun
def clent_html(request):
    users = Users.objects.annotate(
        total_spent=Sum(
            Case(
                When(orders__is_status=Order.OrderStatusChoice.DELIVERED, then=F('orders__items__price') * F('orders__items__count')),
                default=0,
                output_field=IntegerField()
            )
        ),
        order_count=Count('orders', filter=~Q(orders__is_status=Order.OrderStatusChoice.CANCELLED))
    ).filter(user_type=Users.UserTypes.CLENT)
    return render(request, 'admin/mijozlar.html', {'users': users})


#kassa html
def kassa_html(request):
    return render(request, 'admin/kassa.html')


#hisobot html
def hisobothtml(request):
    return render(request, 'admin/hisobot.html')