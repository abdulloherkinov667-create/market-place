from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

from app.views import (
    home_page, profile_page, registratsiya, login_viuw,
    ProductDetailsViuw, logout_html, user_logout, ShopingCartHtml,
    shoping_cart_create, tolov_usullari, delete_product_cart, rasmiylashtirish_prod,
    rasmiylashtirish_prod, upgdate_rasmiylash, order_html, order_details, qollab_quvatlash,
    yetkazib_berish_manzili, istaklar, istak_like_bos, catalog_html, yangi_karta
)

from app.admin_viuw import (
    admin_home, buyurtma_admin, buyurma_details, clent_html, kassa_html,
    hisobothtml, today_income
)

urlpatterns = [
    #admin
    path('admin/', admin.site.urls),
    path('admin_home/', admin_home, name='admin_home'),
    path('buyurtma_admin/', buyurtma_admin, name='buyurtma_admin'),
    path('today_income/', today_income, name='today_income'),
    path('buyurma_details/<int:pk>/', buyurma_details, name='buyurma_details'),
    path('mijozlar/', clent_html, name='mijozlar'),
    path('kassa/', kassa_html, name='kassa'),   
    path('hisobothtml/', hisobothtml, name='hisobothtml'),
        
    #product
    path('', home_page, name='home_page'),
    path('product/<slug:slug>/', ProductDetailsViuw.as_view(), name='product_details'),
    path('rasmiylashtirish/', rasmiylashtirish_prod, name='rasmiylashtiri_sh'),
    path('upgdate_rasmiylash/<int:pk>/', upgdate_rasmiylash, name='upgdate_rasmiylash'),   
    path('catalog_html/', catalog_html, name='catalog_html'),   
    
    #istaklar urllari
    path('istaklar/', istaklar, name='istaklar'),
    path('istak_like_bos/', istak_like_bos, name='istak_like_bos'),
      
    
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
    path('yangi_karta/', yangi_karta, name='yangi_karta'),
    
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