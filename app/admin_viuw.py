from django.utils import timezone

from django.http import JsonResponse
from django.shortcuts import render, redirect, get_list_or_404
from django.contrib import messages
from app.models import UzumProduct, ShopingModel, Users, Order, OrderItem, Kategoriy
from django.core.paginator import Paginator
from django.utils.timezone import localdate, timedelta
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


#admin home uchun mijoz sanoq viuwsi
def get_users_count():
    orders_count = Order.objects.count()

    context = {
        'orders_count': orders_count,
    }
    return JsonResponse(context)



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
#status yetgazildi ga ozgarganda jami qoldiq hisoblanadi!
def kassa_html(request):
    total_balance = OrderItem.objects.filter(
        order__is_status=Order.OrderStatusChoice.DELIVERED
    ).aggregate(
        total=Sum(F('price') * F('count'))
    )['total'] or 0

    #bugungi tushum hisobladim!
    today = timezone.now().date()
    today_in = OrderItem.objects.filter(order__is_status=Order.OrderStatusChoice.DELIVERED,order__created_at__date=today).aggregate(
        total=Sum(F('price') * F('count'))
    )['total'] or 0

    today_out = 0 
    recent_orders = Order.objects.annotate(total=Sum(F('items__price') * F('items__count'))).order_by('-created_at')[:10]

    context = {
        'total_balance': total_balance,
        'today_in': today_in,
        'today_out': today_out,
        'recent_orders': recent_orders,
    }
    return render(request, 'admin/kassa.html', context)


#hisobot html
def hisobothtml(request):
    order_delivered = Order.objects.filter(is_status=Order.OrderStatusChoice.DELIVERED)
    result = order_delivered.aggregate(
        total=Sum(F('items__price') * F('items__count'))
    )
    jami_daromat = result['total'] if result['total'] else 0
    savdo_soni = order_delivered.count()
    
    #xozircha 1 kunlik chiqadi
    oxirgi_oy = timezone.now() - timedelta(days=1)
    #--------------------------------
    
    yangi_savdogarlik = Users.objects.filter(date_joined__gte=oxirgi_oy).count()
    bekor_qil_buy = Order.objects.filter(is_status=Order.OrderStatusChoice.CANCELLED).count()
    kategor = Kategoriy.objects.annotate(p_count=Count('products'))
    
    context = {
        'jami_daromat': jami_daromat,
        'savdo_soni': savdo_soni,
        'yangi_savdogarlik': yangi_savdogarlik,
        'bekor_qil_buy': bekor_qil_buy,
        'kategor': kategor,
    }
    return render(request, 'admin/hisobot.html', context)