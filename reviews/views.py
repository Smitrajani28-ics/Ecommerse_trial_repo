from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from products.models import Product
from orders.models import OrderItem
from .models import Review
from .forms import ReviewForm


@login_required
@require_POST
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)

    if Review.objects.filter(product=product, user=request.user).exists():
        messages.warning(request, 'You have already reviewed this product.')
        return redirect(product.get_absolute_url())

    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.product = product
        review.user = request.user
        review.is_verified_purchase = OrderItem.objects.filter(
            order__user=request.user, product=product, order__payment_status='paid'
        ).exists()
        review.save()
        messages.success(request, 'Review submitted!')
    else:
        messages.error(request, 'Please correct the errors in your review.')

    return redirect(product.get_absolute_url())


@login_required
@require_POST
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    product_url = review.product.get_absolute_url()
    review.delete()
    messages.success(request, 'Review deleted.')
    return redirect(product_url)
