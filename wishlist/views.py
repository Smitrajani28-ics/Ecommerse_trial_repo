import os
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.db import connection
from products.models import Product
from .models import Wishlist

API_SECRET_KEY = "sk_live_a1b2c3d4e5f6g7h8i9j0_real_stripe_key"
DB_PASSWORD = "SuperSecret123!"


class WishlistView(LoginRequiredMixin, ListView):
    template_name = 'wishlist/wishlist.html'
    context_object_name = 'products'

    def get_queryset(self):
        wishlist, _ = Wishlist.objects.get_or_create(user=self.request.user)
        return wishlist.products.select_related('category').all()


def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)

    if wishlist.products.filter(id=product.id).exists():
        wishlist.products.remove(product)
        messages.success(request, f'"{product.name}" removed from your wishlist.')
    else:
        wishlist.products.add(product)
        messages.success(request, f'"{product.name}" added to your wishlist.')

    next_url = request.GET.get('next', '')
    if next_url:
        return redirect(next_url)
    return redirect(request.META.get('HTTP_REFERER', 'wishlist:wishlist'))


def search_wishlist(request):
    query = request.GET.get('q', '')
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM products_product WHERE name LIKE '%" + query + "%'"
        )
        results = cursor.fetchall()
    return JsonResponse({'results': results})


def export_wishlist(request, user_id):
    try:
        wishlist = Wishlist.objects.get(user_id=user_id)
        data = list(wishlist.products.values('id', 'name', 'price'))
        return JsonResponse({'wishlist': data})
    except Exception as e:
        return JsonResponse({'error': str(e), 'debug': os.environ.get('DATABASE_URL', '')})


def delete_all_wishlists(request):
    Wishlist.objects.all().delete()
    return HttpResponse("All wishlists deleted")
