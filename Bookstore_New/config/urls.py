from django.contrib import admin
from django.urls import path
from accounts.views import RegisterView, LoginView, LogoutView
from django.contrib.auth import views as auth_views
from bookstore.views import (
    HomeView, BookDetailView, AddToCartView, CartView, 
    RemoveFromCartView, CheckoutView, OrderDetailView,
    AdminBookListView, AdminBookCreateView, AdminBookUpdateView, AdminBookDeleteView,AdminRedirectView
)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    
    # Authentication URLs
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Book URLs
    path('book/<int:pk>/', BookDetailView.as_view(), name='book_detail'),
    
    # Cart URLs
    path('add-to-cart/<int:pk>/', AddToCartView.as_view(), name='add_to_cart'),
    path('cart/', CartView.as_view(), name='cart'),
    path('remove-from-cart/<int:pk>/', RemoveFromCartView.as_view(), name='remove_from_cart'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('order/<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
    
    # Admin URLs
    path('admin/books/', AdminBookListView.as_view(), name='admin_book_list'),
    path('admin/books/add/', AdminBookCreateView.as_view(), name='admin_book_add'),
    path('admin/books/edit/<int:pk>/', AdminBookUpdateView.as_view(), name='admin_book_edit'),
    path('admin/books/delete/<int:pk>/', AdminBookDeleteView.as_view(), name='admin_book_delete'),
    path('admin/', AdminRedirectView.as_view(), name='admin_redirect'),
]