from django.shortcuts import render
from django.views.generic import TemplateView

class ProductListView(TemplateView):
    template_name = 'products/product_list.html'

class ProductDetailView(TemplateView):
    template_name = 'products/product_detail.html'
