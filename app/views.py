from django.shortcuts import render
from .models import UzumProduct
from django.core.paginator import Paginator
from django.views.generic import (
    ListView, TemplateView, DetailView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from .models import UzumProduct
from .models import Users
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, get_list_or_404


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
class ShopingCartHtml(LoginRequiredMixin, TemplateView):
    template_name = 'products/shoping.html'
    login_url =  'login_viuw'
    

#shoping cartga qoshish uchun
@login_required(login_url='login_viuw')
def shoping_cart_create(request):
    
    if request.method == 'POST':
        data = request.POST
        product_id = data.get('uzumproduct')
        user_id = request.user.id
    
    
    return render(request, 'products/shoping.html')


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