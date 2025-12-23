from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import JsonResponse

class CartDetailView(TemplateView):
    template_name = 'cart/cart_detail.html'

def cart_add(request, product_id):
    return JsonResponse({'status': 'success'})

def cart_remove(request, product_id):
    return JsonResponse({'status': 'success'})

def cart_update(request, product_id):
    return JsonResponse({'status': 'success'})
