"""
URL configuration for market_place project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

from app.views import (
    home_page, profile_page, registratsiya, login_viuw,
    ProductDetailsViuw, logout_html, user_logout, ShopingCartHtml,
    shoping_cart_create, tolov_usullari, delete_product_cart, rasmiylashtirish_prod,
    rasmiylashtirish_prod, upgdate_rasmiylash, order_html, order_details, qollab_quvatlash,
    yetkazib_berish_manzili
)

from app.admin_viuw import (
    admin_home, buyurtma_admin, buyurma_details, clent_html, kassa_html,
    hisobothtml
)

urlpatterns = [
    #admin
    path('admin/', admin.site.urls),
    path('admin_home/', admin_home, name='admin_home'),
    path('buyurtma_admin/', buyurtma_admin, name='buyurtma_admin'),
    path('buyurma_details/<int:pk>/', buyurma_details, name='buyurma_details'),
    path('mijozlar/', clent_html, name='mijozlar'),
    path('kassa/', kassa_html, name='kassa'),
    path('hisobothtml/', hisobothtml, name='hisobothtml'),
    
    #product
    path('', home_page, name='home_page'),
    path('product/<slug:slug>/', ProductDetailsViuw.as_view(), name='product_details'),
    path('rasmiylashtirish/', rasmiylashtirish_prod, name='rasmiylashtiri_sh'),
    path('upgdate_rasmiylash/<int:pk>/', upgdate_rasmiylash, name='upgdate_rasmiylash'),    
    
    #order html
    path('order_html/', order_html, name='order_html'),
    path('order_details/', order_details, name='order_details'),
    
    #profil
    path('profil/', profile_page, name='profile'),
    path('qollab_quvatlash/', qollab_quvatlash, name='qollab_quvatlash'),
    path('yetkazib_berish_manzili/', yetkazib_berish_manzili, name='yetkazib_berish_manzili'),
    
    #shop cart 
    path('shoping_cart/', ShopingCartHtml.as_view(), name='Shoping_Cart_Html'),
    path('shoping_cart_create/', shoping_cart_create, name='shoping_cart_create'),
    path('delete_product_cart/<int:pk>/', delete_product_cart, name='delete_product_cart'),
    path('rasmiylashtirish_prod/', rasmiylashtirish_prod, name='rasmiylashtirish_prod'),
    
    #tolov usullari
    path('tolov_usullari/', tolov_usullari, name='tolov_usullari'),
    
    #registratsiya
    path('registratsiya/', registratsiya, name='registratsiya'),
    path('login_viuw/', login_viuw, name='login_viuw'),
    path('logout/', logout_html, name='logout_html'),
    path('user_logout/', user_logout, name='user_logout'),
    
    #GOOGLE bilan registr qilish uchun url
    path('accounts/', include('allauth.urls')),
    
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )