from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Book, Order, OrderItem
from django.contrib import messages
from django.core.paginator import Paginator
from django.views.generic.base import RedirectView
from django.urls import reverse

class AdminRedirectView(LoginRequiredMixin, UserPassesTestMixin, RedirectView):
    def test_func(self):
        return self.request.user.is_staff
    
    def get_redirect_url(self, *args, **kwargs):
        return reverse('admin_book_list')
    
class HomeView(View):
    template_name = 'bookstore/home.html'
    
    def get(self, request):
        books = Book.objects.all().order_by('-created_at')
        paginator = Paginator(books, 8)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        return render(request, self.template_name, {'page_obj': page_obj})

class BookDetailView(View):
    template_name = 'bookstore/book_detail.html'
    
    def get(self, request, pk):
        book = get_object_or_404(Book, pk=pk)
        return render(request, self.template_name, {'book': book})

class AddToCartView(LoginRequiredMixin, View):
    def post(self, request, pk):
        book = get_object_or_404(Book, pk=pk)
        
        # Initialize cart in session if not exists
        if 'cart' not in request.session:
            request.session['cart'] = {}
        
        cart = request.session['cart']
        book_id = str(book.id)
        
        # Add or update item in cart
        if book_id in cart:
            cart[book_id]['quantity'] += 1
        else:
            cart[book_id] = {
                'title': book.title,
                'price': str(book.price),
                'quantity': 1,
            }
        
        request.session.modified = True
        messages.success(request, f"Added {book.title} to your cart.")
        return redirect('cart')

class CartView(LoginRequiredMixin, View):
    template_name = 'bookstore/cart.html'
    
    def get(self, request):
        cart = request.session.get('cart', {})
        cart_items = []
        total = 0
        
        for book_id, item in cart.items():
            book = get_object_or_404(Book, pk=book_id)
            item_total = book.price * item['quantity']
            total += item_total
            cart_items.append({
                'book': book,
                'quantity': item['quantity'],
                'item_total': item_total,
            })
        
        return render(request, self.template_name, {
            'cart_items': cart_items,
            'total': total,
        })

class RemoveFromCartView(LoginRequiredMixin, View):
    def post(self, request, pk):
        book_id = str(pk)
        if 'cart' in request.session and book_id in request.session['cart']:
            del request.session['cart'][book_id]
            request.session.modified = True
            messages.success(request, "Item removed from cart.")
        return redirect('cart')

class CheckoutView(LoginRequiredMixin, View):
    def post(self, request):
        cart = request.session.get('cart', {})
        if not cart:
            messages.error(request, "Your cart is empty.")
            return redirect('cart')
        
        # Create order
        order = Order.objects.create(user=request.user)
        total = 0
        
        for book_id, item in cart.items():
            book = get_object_or_404(Book, pk=book_id)
            quantity = item['quantity']
            price = book.price
            
            # Check stock
            if book.stock < quantity:
                messages.error(request, f"Not enough stock for {book.title}. Only {book.stock} available.")
                order.delete()
                return redirect('cart')
            
            # Create order item
            OrderItem.objects.create(
                book=book,
                order=order,
                quantity=quantity,
                price=price
            )
            
            # Update book stock
            book.stock -= quantity
            book.save()
            
            total += price * quantity
        
        # Update order total
        order.total = total
        order.is_completed = True
        order.save()
        
        # Clear cart
        del request.session['cart']
        messages.success(request, "Order placed successfully!")
        return redirect('order_detail', pk=order.id)

class OrderDetailView(LoginRequiredMixin, View):
    template_name = 'bookstore/order_detail.html'
    
    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk, user=request.user)
        return render(request, self.template_name, {'order': order})

# Admin Views
class AdminBookListView(UserPassesTestMixin, View):
    template_name = 'bookstore/admin/book_list.html'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get(self, request):
        books = Book.objects.all()
        print("DEBUG: Books in admin view:", books)  # Check if books exist
        return render(request, self.template_name, {'books': books})

class AdminBookCreateView(UserPassesTestMixin, View):
    template_name = 'bookstore/admin/book_form.html'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get(self, request):
        return render(request, self.template_name)
    
    def post(self, request):
        title = request.POST.get('title')
        author = request.POST.get('author')
        description = request.POST.get('description')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        
        # Basic validation
        errors = {}
        if not title:
            errors['title'] = 'Title is required.'
        if not author:
            errors['author'] = 'Author is required.'
        if not price or not price.replace('.', '').isdigit():
            errors['price'] = 'Valid price is required.'
        if not stock or not stock.isdigit():
            errors['stock'] = 'Valid stock quantity is required.'
        
        if errors:
            return render(request, self.template_name, {
                'errors': errors,
                'form_data': request.POST,
            })
        
        # Create book
        book = Book.objects.create(
            title=title,
            author=author,
            description=description,
            price=price,
            stock=int(stock),
        )
        
        # Handle image upload if present
        if 'cover_image' in request.FILES:
            book.cover_image = request.FILES['cover_image']
            book.save()
        
        messages.success(request, 'Book created successfully!')
        return redirect('admin_book_list')

class AdminBookUpdateView(UserPassesTestMixin, View):
    template_name = 'bookstore/admin/book_form.html'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get(self, request, pk):
        book = get_object_or_404(Book, pk=pk)
        return render(request, self.template_name, {'book': book})
    
    def post(self, request, pk):
        book = get_object_or_404(Book, pk=pk)
        
        title = request.POST.get('title')
        author = request.POST.get('author')
        description = request.POST.get('description')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        
        # Basic validation
        errors = {}
        if not title:
            errors['title'] = 'Title is required.'
        if not author:
            errors['author'] = 'Author is required.'
        if not price or not price.replace('.', '').isdigit():
            errors['price'] = 'Valid price is required.'
        if not stock or not stock.isdigit():
            errors['stock'] = 'Valid stock quantity is required.'
        
        if errors:
            return render(request, self.template_name, {
                'errors': errors,
                'book': book,
                'form_data': request.POST,
            })
        
        # Update book
        book.title = title
        book.author = author
        book.description = description
        book.price = price
        book.stock = int(stock)
        
        # Handle image upload if present
        if 'cover_image' in request.FILES:
            book.cover_image = request.FILES['cover_image']
        
        book.save()
        
        messages.success(request, 'Book updated successfully!')
        return redirect('admin_book_list')

class AdminBookDeleteView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff
    
    def post(self, request, pk):
        book = get_object_or_404(Book, pk=pk)
        book.delete()
        messages.success(request, 'Book deleted successfully!')
        return redirect('admin_book_list')