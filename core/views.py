from django.views.generic import TemplateView
from products.models import Product, Category


class HomeView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_products'] = Product.objects.filter(
            is_active=True, is_featured=True
        ).select_related('category')[:8]
        context['categories'] = Category.objects.filter(is_active=True)
        context['latest_products'] = Product.objects.filter(
            is_active=True
        ).select_related('category').order_by('-created_at')[:8]
        return context
