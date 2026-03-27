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
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from app.views import (
    home_page, profile_page, registratsiya, login_viuw,
    ProductDetailsViuw, logout_html, user_logout, ShopingCartHtml
)

urlpatterns = [
    #admin
    path('admin/', admin.site.urls),
    
    #product
    path('', home_page, name='home_page'),
    path('product/<slug:slug>/', ProductDetailsViuw.as_view(), name='product_details'),
    # path('product_details/', product_details, name='product_details'),
    
    #profil
    path('profil/', profile_page, name='profile'),
    
    #shop cart 
    path('shoping_cart/', ShopingCartHtml.as_view(), name='Shoping_Cart_Html'),
    
    #registratsiya
    path('registratsiya/', registratsiya, name='registratsiya'),
    path('login_viuw/', login_viuw, name='login_viuw'),
    path('logout/', logout_html, name='logout_html'),
    path('user_logout/', user_logout, name='user_logout'),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )