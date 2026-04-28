from .models import Wishlist


def wishlist_context(request):
    if request.user.is_authenticated:
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        return {'wishlist_product_ids': set(wishlist.products.values_list('id', flat=True))}
    return {'wishlist_product_ids': set()}
