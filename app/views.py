from django.shortcuts import render
from .models import UzumProduct
from django.core.paginator import Paginator
from .models import Users
from django.shortcuts import render, redirect
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
def product_details(request):
    return render (request, 'product_details.html')


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