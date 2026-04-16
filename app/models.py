import uuid
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class BaseCreatedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Kategoriy(BaseCreatedModel):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name


def default_uzum_info():
    return {"name": "name"}


#product uchun bu!
class UzumProduct(BaseCreatedModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField( max_length=300, unique=True, blank=True, editable=False)
    price = models.PositiveIntegerField()
    aksi_narx = models.PositiveSmallIntegerField( validators=[MinValueValidator(0), MaxValueValidator(100)], default=0)
    about = models.TextField()
    count = models.PositiveIntegerField(default=2)
    is_active = models.BooleanField(default=True)
    info = models.JSONField(default=default_uzum_info, blank=True)
    category = models.ForeignKey(
        Kategoriy,
        on_delete=models.CASCADE,
        related_name='products'
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            while UzumProduct.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"
            self.slug = slug
        super().save(*args, **kwargs)
                

    @property
    def is_new(self):
        return timezone.now() - self.created_at <= timedelta(days=2)

    def __str__(self):
        return self.name

class UzumProductImage(BaseCreatedModel):
    image = models.ImageField(upload_to='maxsulot_rasm/')
    product = models.ForeignKey(UzumProduct, on_delete=models.CASCADE, related_name='images')

    def __str__(self):
        return f"{self.product.name} image"
    

#shoping cart model
class ShopingModel(BaseCreatedModel):
    product = models.ForeignKey(UzumProduct, on_delete=models.CASCADE, related_name='cart_list')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='my_carts')
    
    def __str__(self):
        return self.user.username

#user model
class Users(AbstractUser):
    class UserTypes(models.TextChoices):
        Admin = 'Admin', 'Admin'
        CLENT = 'Clent', 'Mijoz'
        
    avatar = models.ImageField(upload_to='avatar/', blank=True, null=True)
    user_type = models.CharField(max_length=500, choices=UserTypes.choices, default=UserTypes.CLENT)
    phone = models.CharField(max_length=50, blank=True, null=True)
    
    def __str__(self):
        return self.username
    
    @property
    def full_name(self):
        return f"{self.first_name} - {self.last_name}"
    
    
#order model
class Order(BaseCreatedModel):
    class OrderStatusChoice(models.TextChoices):
        PENDING = 'Kutilmoqda', 'Kutilmoqda'          # Buyurtma tushdi, lekin hali ko'rilmadi
        CONFIRMED = 'Tasdiqlandi', 'Tasdiqlandi'     # Admin buyurtmani ko'rib, tasdiqladi
        PROCESSING = 'Tayyorlanmoqda', 'Tayyorlanmoqda' # Omborxonada qadoqlanmoqda
        SHIPPED = 'Yo‘lga chiqdi', 'Yo‘lga chiqdi'       # Kuryerga berildi yoki pochta yo'lida
        DELIVERED = 'Yetkazildi', 'Yetkazildi'      # Mijoz mahsulotni qabul qilib oldi
        CANCELLED = 'Bekor qilindi', 'Bekor qilindi'   # Mijoz yoki admin tomonidan bekor qilindi
        RETURNED = 'Qaytarildi', 'Qaytarildi'
    
    class PaymentMethodChoice(models.TextChoices):
        CASH = 'cash', 'Naqd pul'
        CARD = 'card', 'Plastik karta (Terminal)'
        CLICK = 'click', 'Click'
        PAYME = 'payme', 'Payme'
        UZUM = 'uzum', 'Uzum Bank'
        
    
    karta_nomer = models.CharField(max_length=19) 
    cart_egasi = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='order_banks_carts')
    muddat = models.CharField(max_length=5) 
    cvv = models.CharField(max_length=3)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='orders')
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(verbose_name="Zakar borishi kk bo'lgan manzil", blank=True, null=True)
    description = models.CharField(max_length=500, blank=True, null=True)
    is_status = models.CharField(
        max_length=30,
        choices=OrderStatusChoice.choices,
        default=OrderStatusChoice.PENDING
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethodChoice.choices,
        default=PaymentMethodChoice.CASH,
        verbose_name="To'lov usuli"
    )

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"

    @property
    def total_order_price(self):
        return sum(item.item_total_price for item in self.items.all())
    
    def __str__(self):
        return self.user.username
    
    
#order item model
class OrderItem(BaseCreatedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(UzumProduct, on_delete=models.SET_NULL, related_name="order_items", null=True)
    price = models.BigIntegerField(help_text="Sotib olingan vaqtdagi narxi", editable=False) 
    count = models.IntegerField(validators=[MinValueValidator(1)])


    @property
    def item_total_price(self):
        return self.price * self.count
    
    def __str__(self):
        return self.product.name
    
    def save(self, *args, **kwargs):
        self.price = self.product.price
        return super().save(*args, **kwargs)
    

#like model
class Like(BaseCreatedModel):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='likes')
    product = models.ForeignKey(UzumProduct, on_delete=models.CASCADE, related_name='likes')

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} likes {self.product.name}"


#carta model
class User_carts(BaseCreatedModel):
    karta_nomer = models.CharField(max_length=19) 
    cart_egasi = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='banks_carts')
    muddat = models.CharField(max_length=5) 
    cvv = models.CharField(max_length=3)

    @property
    def masked_number(self):
        clean_number = self.karta_nomer.replace(" ", "")
        if len(clean_number) >= 16:
            return f"{clean_number[:4]} **** **** {clean_number[-4:]}"
        return clean_number

    @property
    def formatted_number(self):
        """Kartani har 4 ta raqamdan keyin joy tashlab ko'rsatadi"""
        clean_number = self.karta_nomer.replace(" ", "")
        return " ".join([clean_number[i:i+4] for i in range(0, len(clean_number), i+4)])

    def __str__(self):
        return f"{self.cart_egasi.username} - {self.masked_number}"