from django.shortcuts import render, redirect, get_list_or_404
from django.contrib import messages
from .models import UzumProduct, ShopingModel, Users, Order, OrderItem
from django.core.paginator import Paginator
from django.views.generic import (
    ListView, TemplateView, DetailView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout


#home html uchun
def home_page(request):
    products_list = UzumProduct.objects.all().order_by('-id') 
    paginator = Paginator(products_list, 20)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'home.html', {'page_obj': page_obj})


#profile html
def profile_page(request):
    return render(request, 'userlar/profile.html')


#product_details htmli uchun
class ProductDetailsViuw(DetailView):
    model = UzumProduct
    template_name = 'products/product_details.html'
    context_object_name = 'uzumproduct'
    slug_field = "slug"
    

#choping ni htmlini korsatish uchun
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
    if request.method == 'POST':
        u_name = request.POST.get('username')
        pass_word = request.POST.get('password')
        
        user = authenticate(request, username=u_name, password=pass_word)
        
        if user is not None:
            login(request, user)
            return redirect('home_page')
        else:
            return render(request, 'login.html', {'eror': "Username yoki parolingiz noto'g'ri"})

    return render(request, 'userlar/login.html')