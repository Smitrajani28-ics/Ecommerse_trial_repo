from django.shortcuts import render
from django.views.generic import TemplateView

class OrderCreateView(TemplateView):
    template_name = 'orders/order_create.html'

class OrderHistoryView(TemplateView):
    template_name = 'orders/order_history.html'

class OrderDetailView(TemplateView):
    template_name = 'orders/order_detail.html'
