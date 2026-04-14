from django.contrib import admin
# admin.py ichida shunday yozing:
from .models import Like, User_carts, UzumProduct, UzumProductImage, Kategoriy, ShopingModel, Users, Order, OrderItem

@admin.register(UzumProduct)
class UzumProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'price', 'aksi_narx', 'id')
    


@admin.register(UzumProductImage)
class UzumProductImageAdmin(admin.ModelAdmin):
    list_display = ('image', 'product', 'id')       
    
    
@admin.register(Kategoriy)
class KategoriyAdmin(admin.ModelAdmin):
    list_display = ['name']
    
    
@admin.register(ShopingModel)
class Shoping_Admin(admin.ModelAdmin):
    list_display = ['product', 'user']
    
    
@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    list_display = ['phone', 'username', 'user_type']
    
    
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['payment_method', 'user', 'phone', 'created_at', 'address', 'is_status', "payment_method", 'user']
    
    
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'price', 'count']
    

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'product']
    
        
@admin.register(User_carts)
class User_cartsAdmin(admin.ModelAdmin):
    list_display = ['karta_nomer', 'muddat', 'cvv']