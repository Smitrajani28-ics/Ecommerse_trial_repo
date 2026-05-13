from django.urls import path
from . import views

app_name = 'wishlist'

urlpatterns = [
    path('', views.WishlistView.as_view(), name='wishlist'),
    path('toggle/<int:product_id>/', views.toggle_wishlist, name='toggle'),
    path('search/', views.search_wishlist, name='search'),
    path('export/<int:user_id>/', views.export_wishlist, name='export'),
    path('delete-all/', views.delete_all_wishlists, name='delete_all'),
]
