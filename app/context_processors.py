from .models import ShopingModel


def cart_item_count(request):
    count = 0
    if request.user.is_authenticated:
        count = ShopingModel.objects.filter(user=request.user).count()
    return {'cart_item_count': count}
