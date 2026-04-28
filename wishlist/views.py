from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from products.models import Product
from .models import Wishlist


class WishlistView(LoginRequiredMixin, ListView):
    template_name = 'wishlist/wishlist.html'
    context_object_name = 'products'

    def get_queryset(self):
        wishlist, _ = Wishlist.objects.get_or_create(user=self.request.user)
        return wishlist.products.select_related('category').all()


@login_required
@require_POST
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)

    if wishlist.products.filter(id=product.id).exists():
        wishlist.products.remove(product)
        messages.success(request, f'"{product.name}" removed from your wishlist.')
    else:
        wishlist.products.add(product)
        messages.success(request, f'"{product.name}" added to your wishlist.')

    return redirect(request.META.get('HTTP_REFERER', 'wishlist:wishlist'))
