from unicodedata import name
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render, redirect, get_list_or_404
from django.contrib import messages
from django.db.models import Q
from .models import UzumProduct, ShopingModel, Users, Order, OrderItem, Like
from django.core.paginator import Paginator
from django.views.generic import (
    ListView, TemplateView, DetailView
)

from django.shortcuts import render
import requests
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout

TOKEN = "8664343682:AAF1kA0nwrIeLZjwUsbV97Za_J1Ry90sGBc"
ADMIN_ID = [6411347321, 8327989068]

#home html uchun
def home_page(request):
    query = ''
    products_list = UzumProduct.objects.all().order_by('-id')

    # search uchun
    if request.method == 'POST':
        query = request.POST.get('q', '').strip()
        if query:
            products_list = products_list.filter(
                Q(name__icontains=query) | Q(about__icontains=query)
            )

    # Sahifalashni sozlash
    paginator = Paginator(products_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Foydalanuvchining yoqtirgan mahsulotlari 
    liked_product_ids = []
    if request.user.is_authenticated:
        liked_product_ids = list(Like.objects.filter(user=request.user).values_list('product_id', flat=True))

    return render(request, 'home.html', {
        'page_obj': page_obj,
        'liked_product_ids': liked_product_ids,
        'search_query': query,
    })


#profile html
def profile_page(request):
    return render(request, 'userlar/profile.html')


#product_details htmli uchun
class ProductDetailsViuw(DetailView):
    model = UzumProduct
    template_name = 'products/product_details.html'
    context_object_name = 'uzumproduct'
    slug_field = "slug"
    

#shoping ni htmlini korsatish uchun
class ShopingCartHtml(LoginRequiredMixin, ListView): 
    model = ShopingModel
    template_name = 'products/shoping.html'
    context_object_name = 'cart_items'
    login_url = 'login_viuw'

    def get_queryset(self):
        return ShopingModel.objects.filter(user=self.request.user).select_related('product')
    
    
#shoping cartdagi malumotlarni ochirish uchun
@login_required(login_url='login_viuw')
def delete_product_cart(request, pk):
    product_id = pk
    user_id = request.user.id
    db_cart = ShopingModel.objects.filter(id=product_id, user_id=user_id)
    
    if db_cart.exists():
        db_cart.delete()
        return redirect('Shoping_Cart_Html')
    return redirect('Shoping_Cart_Html')
    

#shoping cartga qoshish uchun
@login_required(login_url='login_viuw')
def shoping_cart_create(request):
    
    if request.method == 'POST':
        data = request.POST
        product_id = data.get('uzumproduct')
        user_id = request.user.id
        print(product_id, user_id)
        
        new_cart = ShopingModel.objects.create(
            product_id=product_id,
            user_id=user_id
        )
        new_cart.save()
        messages.success(request, "Mahsulot savatga qo'shildi!")
        
        return redirect('home_page')
    

#rasmylashtirish html
@login_required()
def rasmiylashtirish_prod(request):
    new_order = Order.objects.create(user_id = request.user.id)
    new_order.save()
    
    order_id = new_order.id
    order_item_list = request.user.my_carts
    
    for i in order_item_list.all():
        new_order_item = OrderItem.objects.create(
            order_id = order_id,
            count = 1,
            product_id = i.product_id
        )
        
        new_order_item.save()
        cart_delete = ShopingModel.objects.filter(id=i.id)
        cart_delete.delete()
        
    # Buyurtma rasmiylashtirildi xabari (qizil rangga mos error/class bilan ko‘rsatiladi)
    messages.error(request, "Buyurtmangiz muvaffaqiyatli berildi! Tez orada yetkazib beramiz.")
    return render(request, 'products/rasmiyla_sh.html', context={ "order": new_order })


#upgdate qilish jarayoni
def upgdate_rasmiylash(request, pk):
    if request.method == 'POST':
        data = request.POST
        
        phone = data.get('phone_number')
        address = data.get('address')
        description = data.get('notes')
        payment_method = data.get('payment_method')
        
        db_order = Order.objects.filter(id=pk).first()
        
        if db_order:
            db_order.phone = phone
            db_order.address = address
            db_order.description = description
            db_order.payment_method = payment_method
            db_order.is_status = Order.OrderStatusChoice.CONFIRMED
            db_order.save()
            
            from django.contrib import messages
            messages.success(request, "Buyurtmangiz muvaffaqiyatli rasmiylashtirildi! Tez orada siz bilan bog'lanamiz.")
        
        return redirect('home_page')
    
    
#tolov usullari html
def tolov_usullari(request):
    return render(request, 'userlar/tolov_usul.html')


#order html uchun
@login_required(login_url='login_viuw')
def order_html(request):
    return render(request, 'products/order_list.html')   


#order details html
@login_required(login_url='login_viuw')
def order_details(request):
    return render(request, 'products/order_details.html')


#logout html
def logout_html(request):
    return render(request, 'userlar/logout.html')


#registratsiya html
def registratsiya(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        
        if username and phone and password:
            Users.objects.create_user(username=username, phone=phone, password=password)
            return redirect('login_viuw')
    return render(request, 'userlar/registratsiy.html')


#user logout
def user_logout(request):
    logout(request)
    return redirect('login_viuw')


#login html uchun
def login_viuw(request):
    
    if request.user.is_authenticated:
        return redirect('home_page')
    
    
    if request.method == 'POST':
        u_name = request.POST.get('username')
        pass_word = request.POST.get('password')
        
        
        user = authenticate(request, username=u_name, password=pass_word)
        
        if user is not None:
            login(request, user)
            messages.success(request, "muvaffaqiyatli tizimga kirdingiz!")
            
            if user.user_type == Users.UserTypes.Admin:
                return redirect('admin_home')
            else:
                return redirect("home_page")

    return render(request, 'userlar/login.html')


#yetkazib berish manzili html
def yetkazib_berish_manzili(request):
    return render(request, 'userlar/yetgazish_manzil.html')


#katalog html 
def catalog_html(request):
    return render(request, 'products/katalog.html')


#qiqruv viuw
# def search(request):
#     if request.method == 'POST':
#         search_query = request.POST.get('search_query')
#         products_list = UzumProduct.objects.filter(name__icontains=search_query).order_by('-id')
#         paginator = Paginator(products_list, 20)


#ISTAKLAR HTML
@login_required(login_url='login_viuw')
def istaklar(request):
    products = UzumProduct.objects.filter(
        likes__user=request.user
    ).distinct()

    return render(request, 'products/istak.html', {
        'page_obj': products
    })


#istaklar like qilish uchun
@login_required(login_url='login_viuw')
def istak_like_bos(request):
    if request.method == 'POST':    
        product_id = request.POST.get('product_id')
        product = get_object_or_404(UzumProduct, id=product_id)
        like = Like.objects.filter(user=request.user, product=product)
        
        if like.exists():
            like.delete()
        else:
            like = Like.objects.create(user=request.user, product=product)
            like.save()
        return redirect('home_page')
    
    
#yangi karta qoshish uchun html
def yangi_karta(request):
    return render(request, 'userlar/yngi_cart_qos.html')





#------------------bot qismim------------------
# qo‘llab-quvvatlash (support)
def qollab_quvatlash(request):
    if request.method == 'POST':
        submit = request.POST.get('message')

        bot_text = f"""
📩 Hurmatli ADMIN YANGI MUROJAAT:

👤 Foydalanuvchi: {request.user.username}
🆔 ID: {request.user.id}

💬 Xabar:
{submit}
        """

        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {
            "chat_id": ADMIN_ID,
            "text": bot_text
        }

        requests.post(url, data=data)

    return render(request, 'userlar/support_page.html')