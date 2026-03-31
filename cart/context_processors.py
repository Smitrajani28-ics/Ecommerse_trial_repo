from .models import Cart


def cart_context(request):
    """Make cart available in all templates."""
    cart = None
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
    elif request.session.session_key:
        cart = Cart.objects.filter(
            session_key=request.session.session_key, user__isnull=True
        ).first()
    return {'cart': cart}
