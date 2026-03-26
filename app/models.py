import uuid
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import AbstractUser


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