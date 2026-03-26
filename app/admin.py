from django.contrib import admin
from .models import UzumProduct, UzumProductImage, Kategoriy



@admin.register(UzumProduct)
class UzumProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'price', 'aksi_narx', 'id')
    


@admin.register(UzumProductImage)
class UzumProductImageAdmin(admin.ModelAdmin):
    list_display = ('image', 'product', 'id')
    
    
@admin.register(Kategoriy)
class KategoriyAdmin(admin.ModelAdmin):
    list_display = ['name']
        