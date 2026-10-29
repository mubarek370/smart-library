from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.utils import timezone
from django.http import JsonResponse
from django.conf import settings
from datetime import datetime, timedelta
from ..books.models import Book, Category
from ..borrow.models import BorrowRecord, BookRequest
from ..users.models import User
from ..users.permissions import admin_required, librarian_or_admin_required, student_required


@login_required
@admin_required
def admin_dashboard(request):
    """Admin dashboard with comprehensive statistics"""
    from django.core.cache import cache
    context = cache.get('admin_dashboard_context')
    if not context:
        # Basic counts
        total_books = Book.objects.count()
        total_categories = Category.objects.count()
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        
        # User role breakdown
        admin_count = User.objects.filter(role='admin').count()
        librarian_count = User.objects.filter(role='librarian').count()
        student_count = User.objects.filter(role='student').count()
        
        # Book statistics
        available_books = Book.objects.filter(available_copies__gt=0).count()
        unavailable_books = Book.objects.filter(available_copies=0).count()
        total_copies = Book.objects.aggregate(total=Sum('total_copies'))['total'] or 0
        available_copies = Book.objects.aggregate(total=Sum('available_copies'))['total'] or 0
        
        # Borrow statistics
        total_borrows = BorrowRecord.objects.count()
        active_borrows = BorrowRecord.objects.filter(status__in=['borrowed', 'overdue']).count()
        overdue_books = BorrowRecord.objects.filter(status='overdue').count()
        returned_books = BorrowRecord.objects.filter(status='returned').count()
        
        # Pending requests
        pending_requests = BookRequest.objects.filter(status='pending').count()
        
        # Financial data
        total_fines = BorrowRecord.objects.filter(fine_amount__gt=0).aggregate(
            total=Sum('fine_amount'))['total'] or 0
        unpaid_fines = BorrowRecord.objects.filter(
            fine_amount__gt=0, fine_paid=False
        ).aggregate(total=Sum('fine_amount'))['total'] or 0
        
        # Recent activity
        recent_borrows = list(BorrowRecord.objects.select_related('user', 'book').order_by('-borrow_date')[:10])
        recent_returns = list(BorrowRecord.objects.filter(status='returned').select_related('user', 'book').order_by('-return_date')[:10])
        
        # Most popular books
        most_borrowed = list(Book.objects.filter(times_borrowed__gt=0).order_by('-times_borrowed')[:10])
        
        # Monthly statistics for charts
        today = timezone.now().date()
        last_30_days = today - timedelta(days=30)
        
        monthly_borrows = list(BorrowRecord.objects.filter(
            borrow_date__gte=last_30_days
        ).values('borrow_date__date').annotate(count=Count('id')).order_by('borrow_date__date'))
        
        context = {
            # Basic stats
            'total_books': total_books,
            'total_categories': total_categories,
            'total_users': total_users,
            'active_users': active_users,
            
            # User breakdown
            'admin_count': admin_count,
            'librarian_count': librarian_count,
            'student_count': student_count,
            
            # Book stats
            'available_books': available_books,
            'unavailable_books': unavailable_books,
            'total_copies': total_copies,
            'available_copies': available_copies,
            
            # Borrow stats
            'total_borrows': total_borrows,
            'active_borrows': active_borrows,
            'overdue_books': overdue_books,
            'returned_books': returned_books,
            'pending_requests': pending_requests,
            
            # Financial
            'total_fines': total_fines,
            'unpaid_fines': unpaid_fines,
            
            # Recent activity
            'recent_borrows': recent_borrows,
            'recent_returns': recent_returns,
            'most_borrowed': most_borrowed,
            
            # Chart data
            'monthly_borrows': monthly_borrows,
        }
        cache.set('admin_dashboard_context', context, 30)
    
    return render(request, 'dashboard/admin_dashboard.html', context)


def home(request):
    """Home/Landing page - accessible to everyone, but redirect authenticated users to their dashboard"""
    # Redirect authenticated users to their role-specific dashboard
    if request.user.is_authenticated:
        if request.user.is_admin:
            return redirect('dashboard:admin')
        elif request.user.is_librarian:
            return redirect('dashboard:librarian')
        elif request.user.is_student:
            return redirect('dashboard:student')
    
    from django.core.cache import cache
    context = cache.get('landing_page_context')
    if not context:
        # Get statistics for landing page
        from django.db.models import Count
        from datetime import timedelta
        
        total_books = Book.objects.count()
        total_users = User.objects.filter(is_active=True).count()
        
        # Calculate daily borrows (average or today's count)
        today = timezone.now().date()
        daily_borrows = BorrowRecord.objects.filter(borrow_date__date=today).count()
        
        # If no borrows today, show average from last 30 days
        if daily_borrows == 0:
            last_30_days = today - timedelta(days=30)
            total_borrows_30_days = BorrowRecord.objects.filter(borrow_date__date__gte=last_30_days).count()
            daily_borrows = total_borrows_30_days // 30 if total_borrows_30_days > 0 else 0
        
        # Get category statistics
        categories_stats = list(Category.objects.annotate(
            book_count=Count('books')
        ).order_by('-book_count')[:6])
        
        # Get featured books for the landing page — books with covers first, then fill with others
        featured_books_with_cover = list(
            Book.objects.filter(
                available_copies__gt=0
            ).exclude(cover_image='').exclude(cover_image__isnull=True)
            .select_related('category').order_by('-times_borrowed', '-rating')[:6]
        )
        if len(featured_books_with_cover) < 6:
            existing_ids = [b.id for b in featured_books_with_cover]
            fallback = list(
                Book.objects.filter(available_copies__gt=0)
                .exclude(id__in=existing_ids)
                .select_related('category').order_by('-times_borrowed', '-rating')[:6 - len(featured_books_with_cover)]
            )
            featured_books = featured_books_with_cover + fallback
        else:
            featured_books = featured_books_with_cover

        # Get 3 books for hero floating animation — prefer books with covers
        hero_books = list(
            Book.objects.exclude(cover_image='').exclude(cover_image__isnull=True)
            .select_related('category').order_by('-times_borrowed', '-rating')[:3]
        )
        if len(hero_books) < 3:
            existing_ids = [b.id for b in hero_books]
            fallback_hero = list(
                Book.objects.exclude(id__in=existing_ids)
                .select_related('category').order_by('-times_borrowed', '-rating')[:3 - len(hero_books)]
            )
            hero_books = hero_books + fallback_hero
        
        context = {
            'total_books': total_books,
            'total_users': total_users,
            'daily_borrows': daily_borrows,
            'categories_stats': categories_stats,
            'featured_books': featured_books,
            'hero_books': hero_books,
            'borrowed_books': [],
        }
        cache.set('landing_page_context', context, 60)
    
    return render(request, 'dashboard/home.html', context)


@login_required
@librarian_or_admin_required
def librarian_dashboard(request):
    from django.core.cache import cache
    context = cache.get('librarian_dashboard_context')
    if not context:
        # Book management stats
        total_books = Book.objects.count()
        available_books = Book.objects.filter(available_copies__gt=0).count()
        low_stock_books = list(Book.objects.filter(available_copies__lte=2, available_copies__gt=0))
        out_of_stock_books = Book.objects.filter(available_copies=0).count()
        
        # Borrow management stats
        active_borrows = BorrowRecord.objects.filter(status__in=['borrowed', 'overdue']).count()
        overdue_books = BorrowRecord.objects.filter(status='overdue').count()
        pending_requests = BookRequest.objects.filter(status='pending').count()
        approved_requests = BookRequest.objects.filter(status='ready').count()
        
        # Today's activity
        today = timezone.now().date()
        todays_borrows = BorrowRecord.objects.filter(borrow_date__date=today).count()
        todays_returns = BorrowRecord.objects.filter(return_date=today).count()
        todays_requests = BookRequest.objects.filter(request_date__date=today).count()
        
        # Recent activity for librarian attention
        recent_borrows = list(BorrowRecord.objects.select_related('user', 'book').order_by('-borrow_date')[:10])
        recent_requests = list(BookRequest.objects.filter(status='pending').select_related('user', 'book').order_by('-request_date')[:10])
        overdue_records = list(BorrowRecord.objects.filter(status='overdue').select_related('user', 'book').order_by('due_date')[:10])
        
        # Books needing attention
        popular_books = list(Book.objects.filter(available_copies__lte=2).order_by('-times_borrowed')[:5])
        
        # Fine collection
        total_fines_pending = BorrowRecord.objects.filter(
            fine_amount__gt=0, fine_paid=False
        ).aggregate(total=Sum('fine_amount'))['total'] or 0
        
        context = {
            # Book stats
            'total_books': total_books,
            'available_books': available_books,
            'low_stock_books': low_stock_books,
            'out_of_stock_books': out_of_stock_books,
            'low_stock_count': len(low_stock_books),
            
            # Borrow stats
            'active_borrows': active_borrows,
            'overdue_books': overdue_books,
            'pending_requests': pending_requests,
            'approved_requests': approved_requests,
            
            # Today's activity
            'todays_borrows': todays_borrows,
            'todays_returns': todays_returns,
            'todays_requests': todays_requests,
            
            # Recent activity
            'recent_borrows': recent_borrows,
            'recent_requests': recent_requests,
            'overdue_records': overdue_records,
            'popular_books': popular_books,
            
            # Financial
            'total_fines_pending': total_fines_pending,
        }
        cache.set('librarian_dashboard_context', context, 30)
    
    return render(request, 'dashboard/librarian_dashboard.html', context)


@login_required
@student_required
def student_dashboard(request):
    """Student dashboard with personal library information"""
    user = request.user
    
    # Personal borrow statistics
    borrowed_books = BorrowRecord.objects.filter(user=user, status__in=['borrowed', 'overdue']).select_related('book')
    borrow_history = BorrowRecord.objects.filter(user=user).select_related('book').order_by('-borrow_date')
    overdue_books = BorrowRecord.objects.filter(user=user, status='overdue').select_related('book')
    
    # Request statistics
    pending_requests = BookRequest.objects.filter(user=user, status='pending').select_related('book')
    approved_requests = BookRequest.objects.filter(user=user, status='ready').select_related('book')
    
    # Personal stats
    total_books_borrowed = borrow_history.count()
    books_returned = BorrowRecord.objects.filter(user=user, status='returned').count()
    current_borrowed_count = borrowed_books.count()
    
    # Fine information
    total_fines = BorrowRecord.objects.filter(user=user, fine_amount__gt=0).aggregate(
        total=Sum('fine_amount'))['total'] or 0
    unpaid_fines = BorrowRecord.objects.filter(
        user=user, fine_amount__gt=0, fine_paid=False
    ).aggregate(total=Sum('fine_amount'))['total'] or 0
    
    # Recommendations based on user's reading history
    user_categories = borrow_history.values_list('book__category', flat=True).distinct()
    recommended_books = Book.objects.filter(
        category__in=user_categories,
        available_copies__gt=0
    ).exclude(
        id__in=borrowed_books.values_list('book_id', flat=True)
    ).order_by('-times_borrowed')[:6]
    
    # If no history-based recommendations, show popular books
    if not recommended_books.exists():
        recommended_books = Book.objects.filter(
            available_copies__gt=0
        ).order_by('-times_borrowed')[:6]
    
    # Due dates and alerts
    books_due_soon = borrowed_books.filter(
        due_date__lte=timezone.now().date() + timedelta(days=3)
    ).order_by('due_date')
    
    # Reading progress (books borrowed this month)
    this_month = timezone.now().replace(day=1).date()
    books_this_month = BorrowRecord.objects.filter(
        user=user, 
        borrow_date__gte=this_month
    ).count()
    
    context = {
        # Current status
        'borrowed_books': borrowed_books,
        'pending_requests': pending_requests,
        'approved_requests': approved_requests,
        'overdue_books': overdue_books,
        'books_due_soon': books_due_soon,
        
        # Statistics
        'total_books_borrowed': total_books_borrowed,
        'books_returned': books_returned,
        'current_borrowed_count': current_borrowed_count,
        'books_this_month': books_this_month,
        'max_limit': request.user.profile.max_books_allowed,
        'remaining_slots': request.user.profile.max_books_allowed - current_borrowed_count,
        
        # Financial
        'total_fines': total_fines,
        'unpaid_fines': unpaid_fines,
        
        # Recommendations
        'recommended_books': recommended_books,
        'borrow_history': borrow_history[:10],  # Recent 10
    }
    
    return render(request, 'dashboard/student_dashboard.html', context)


@login_required
@admin_required
def analytics(request):
    """Analytics view for admin with real chart data"""
    from django.db.models import Count, Sum
    from datetime import timedelta

    today = timezone.now().date()

    # Last 12 months borrow trend
    monthly_labels = []
    monthly_data = []
    for i in range(11, -1, -1):
        month_start = (today.replace(day=1) - timedelta(days=30 * i))
        month_start = month_start.replace(day=1)
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1, day=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1, day=1)
        count = BorrowRecord.objects.filter(
            borrow_date__date__gte=month_start,
            borrow_date__date__lt=month_end
        ).count()
        monthly_labels.append(month_start.strftime('%b %Y'))
        monthly_data.append(count)

    # Category distribution
    category_stats = list(Category.objects.annotate(
        book_count=Count('books'),
        borrow_count=Count('books__borrow_records')
    ).values('name', 'book_count', 'borrow_count').order_by('-borrow_count'))

    # User role distribution
    role_stats = {
        'admin': User.objects.filter(role='admin').count(),
        'librarian': User.objects.filter(role='librarian').count(),
        'student': User.objects.filter(role='student').count(),
    }

    # Book availability
    available_books = Book.objects.filter(available_copies__gt=0).count()
    unavailable_books = Book.objects.filter(available_copies=0).count()

    # Last 7 days daily activity
    daily_labels = []
    daily_borrows = []
    daily_returns = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        daily_labels.append(day.strftime('%a %d'))
        daily_borrows.append(BorrowRecord.objects.filter(borrow_date__date=day).count())
        daily_returns.append(BorrowRecord.objects.filter(return_date=day).count())

    # Top 10 most borrowed books
    top_books = Book.objects.filter(times_borrowed__gt=0).order_by('-times_borrowed')[:10]

    # Summary stats
    total_fines = BorrowRecord.objects.filter(fine_amount__gt=0).aggregate(t=Sum('fine_amount'))['t'] or 0
    unpaid_fines = BorrowRecord.objects.filter(fine_amount__gt=0, fine_paid=False).aggregate(t=Sum('fine_amount'))['t'] or 0

    import json
    context = {
        'monthly_labels_json': json.dumps(monthly_labels),
        'monthly_data_json': json.dumps(monthly_data),
        'category_stats': category_stats,
        'role_stats': role_stats,
        'available_books': available_books,
        'unavailable_books': unavailable_books,
        'daily_labels_json': json.dumps(daily_labels),
        'daily_borrows_json': json.dumps(daily_borrows),
        'daily_returns_json': json.dumps(daily_returns),
        'top_books': top_books,
        'total_fines': total_fines,
        'unpaid_fines': unpaid_fines,
    }
    return render(request, 'dashboard/analytics.html', context)


@login_required
@admin_required
def reports(request):
    """Reports view for admin"""
    from django.db.models import Sum, Count
    from datetime import timedelta

    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)

    # This month stats
    this_month_borrows = BorrowRecord.objects.filter(borrow_date__date__gte=this_month_start).count()
    this_month_returns = BorrowRecord.objects.filter(return_date__gte=this_month_start).count()
    this_month_requests = BookRequest.objects.filter(request_date__date__gte=this_month_start).count()
    this_month_fines = BorrowRecord.objects.filter(
        fine_amount__gt=0, borrow_date__date__gte=this_month_start
    ).aggregate(t=Sum('fine_amount'))['t'] or 0

    # Last month stats
    last_month_borrows = BorrowRecord.objects.filter(
        borrow_date__date__gte=last_month_start,
        borrow_date__date__lt=this_month_start
    ).count()

    # Overall stats
    total_borrows = BorrowRecord.objects.count()
    total_fines = BorrowRecord.objects.filter(fine_amount__gt=0).aggregate(t=Sum('fine_amount'))['t'] or 0
    unpaid_fines = BorrowRecord.objects.filter(fine_amount__gt=0, fine_paid=False).aggregate(t=Sum('fine_amount'))['t'] or 0
    total_users = User.objects.count()
    total_books = Book.objects.count()

    # Top borrowed books (all time)
    top_books = Book.objects.filter(times_borrowed__gt=0).order_by('-times_borrowed')[:10]

    # Most active students
    top_students = User.objects.filter(role='student').annotate(
        borrow_count=Count('borrow_records')
    ).filter(borrow_count__gt=0).order_by('-borrow_count')[:10]

    # Overdue summary
    overdue_count = BorrowRecord.objects.filter(status='overdue').count()
    overdue_fines = BorrowRecord.objects.filter(
        status='overdue', fine_amount__gt=0
    ).aggregate(t=Sum('fine_amount'))['t'] or 0

    context = {
        'this_month_borrows': this_month_borrows,
        'this_month_returns': this_month_returns,
        'this_month_requests': this_month_requests,
        'this_month_fines': this_month_fines,
        'last_month_borrows': last_month_borrows,
        'total_borrows': total_borrows,
        'total_fines': total_fines,
        'unpaid_fines': unpaid_fines,
        'total_users': total_users,
        'total_books': total_books,
        'top_books': top_books,
        'top_students': top_students,
        'overdue_count': overdue_count,
        'overdue_fines': overdue_fines,
        'this_month': this_month_start,
    }
    return render(request, 'dashboard/reports.html', context)


@login_required
def calendar_view(request):
    """Calendar view showing due dates and library events"""
    from django.utils import timezone
    import json
    
    # Get borrow records with due dates
    if request.user.is_student:
        # Students see only their own due dates
        records = BorrowRecord.objects.filter(
            user=request.user,
            status__in=['borrowed', 'overdue']
        ).select_related('book')
    else:
        # Staff see all due dates
        records = BorrowRecord.objects.filter(
            status__in=['borrowed', 'overdue']
        ).select_related('user', 'book')
    
    # Prepare calendar events
    events = []
    for record in records:
        color = '#dc3545' if record.status == 'overdue' else '#28a745'  # Red for overdue, green for normal
        
        if request.user.is_student:
            title = f"Return: {record.book.title}"
        else:
            title = f"{record.user.username}: {record.book.title}"
        
        events.append({
            'title': title,
            'start': record.due_date.isoformat(),
            'color': color,
            'url': f'/books/{record.book.pk}/',
            'extendedProps': {
                'user': record.user.username,
                'book': record.book.title,
                'status': record.status,
                'fine': float(record.fine_amount) if record.fine_amount else 0
            }
        })
    
    context = {
        'events_json': json.dumps(events),
        'events': events
    }
    
    return render(request, 'dashboard/calendar.html', context)

@login_required
@admin_required
def dashboard_stats_api(request):
    """API endpoint for dashboard statistics (for charts)"""
    from django.db.models import Count, Sum
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    # Basic stats
    stats = {
        'total_books': Book.objects.count(),
        'total_users': User.objects.count(),
        'active_borrows': BorrowRecord.objects.filter(status__in=['borrowed', 'overdue']).count(),
        'overdue_books': BorrowRecord.objects.filter(status='overdue').count(),
    }
    
    # Monthly borrow trends (last 12 months)
    today = timezone.now().date()
    twelve_months_ago = today - timedelta(days=365)
    
    monthly_borrows = []
    for i in range(12):
        month_start = today.replace(day=1) - timedelta(days=30*i)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        count = BorrowRecord.objects.filter(
            borrow_date__date__gte=month_start,
            borrow_date__date__lte=month_end
        ).count()
        
        monthly_borrows.append({
            'month': month_start.strftime('%b %Y'),
            'count': count
        })
    
    monthly_borrows.reverse()  # Show oldest to newest
    
    # Category distribution
    category_stats = Category.objects.annotate(
        book_count=Count('books')
    ).values('name', 'book_count')
    
    # User role distribution
    role_stats = User.objects.values('role').annotate(
        count=Count('id')
    ).order_by('role')
    
    # Book status distribution
    available_books = Book.objects.filter(available_copies__gt=0).count()
    unavailable_books = Book.objects.filter(available_copies=0).count()
    
    # Recent activity (last 7 days)
    week_ago = today - timedelta(days=7)
    daily_activity = []
    
    for i in range(7):
        day = week_ago + timedelta(days=i)
        borrows = BorrowRecord.objects.filter(borrow_date__date=day).count()
        returns = BorrowRecord.objects.filter(return_date=day).count()
        
        daily_activity.append({
            'date': day.strftime('%Y-%m-%d'),
            'day': day.strftime('%a'),
            'borrows': borrows,
            'returns': returns
        })
    
    return JsonResponse({
        'stats': stats,
        'monthly_borrows': monthly_borrows,
        'category_stats': list(category_stats),
        'role_stats': list(role_stats),
        'book_status': {
            'available': available_books,
            'unavailable': unavailable_books
        },
        'daily_activity': daily_activity
    })
    

@login_required
def generate_library_card_view(request, user_id):
    """Generate and download library card for a user"""
    from django.http import HttpResponse
    from .utils import generate_library_card
    from ..users.models import User
    
    user = get_object_or_404(User, pk=user_id)
    
    # Allow users to download their own card, or admins to download any card
    if not (request.user.id == user_id or request.user.is_admin):
        messages.error(request, 'You can only download your own library card.')
        return redirect('users:profile')
    
    # Generate card
    card_image = generate_library_card(user)
    
    # Save to response
    response = HttpResponse(content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="library_card_{user.username}.png"'
    card_image.save(response, 'PNG')
    
    # Log activity
    from .utils import log_activity
    log_activity(request.user, 'other', f'Downloaded library card for {user.username}', request)
    
    return response


@login_required
def view_library_card(request, user_id):
    """View library card as image (not download)"""
    from django.http import HttpResponse
    from .utils import generate_library_card
    from ..users.models import User
    
    user = get_object_or_404(User, pk=user_id)
    
    # Allow users to view their own card, or admins to view any card
    if not (request.user.id == user_id or request.user.is_admin):
        messages.error(request, 'You can only view your own library card.')
        return redirect('users:profile')
    
    # Generate card
    card_image = generate_library_card(user)
    
    # Return as inline image (not download)
    response = HttpResponse(content_type='image/png')
    card_image.save(response, 'PNG')
    
    return response


@login_required
@admin_required
def download_qr_code(request, book_id):
    """Download QR code for a book"""
    from django.http import HttpResponse, Http404, HttpResponseRedirect
    from ..books.models import Book

    book = get_object_or_404(Book, pk=book_id)

    if not book.qr_code:
        # Generate QR code if it doesn't exist
        book.generate_qr_code()
        book.save()

    if book.qr_code:
        storage = book.qr_code.storage
        is_cloudinary = 'cloudinary' in type(storage).__module__.lower()

        if is_cloudinary:
            # On Cloudinary: redirect to the remote URL — browser downloads it
            return HttpResponseRedirect(book.qr_code.url)
        else:
            # Local storage: read and serve from disk
            response = HttpResponse(book.qr_code.read(), content_type='image/png')
            response['Content-Disposition'] = f'attachment; filename="qr_code_{book.isbn}.png"'
            return response
    else:
        raise Http404("QR code not available")


@login_required
@admin_required
def export_overdue_csv(request):
    """Export overdue books to CSV"""
    from django.http import HttpResponse
    from ..borrow.models import BorrowRecord
    import csv
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="overdue_books.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['User', 'Email', 'Book', 'ISBN', 'Due Date', 'Days Overdue', 'Fine (ETB)', 'Fine Paid'])
    
    records = BorrowRecord.objects.filter(status='overdue').select_related('user', 'book')
    
    for record in records:
        writer.writerow([
            record.user.get_full_name() or record.user.username,
            record.user.email,
            record.book.title,
            record.book.isbn,
            record.due_date.strftime('%Y-%m-%d'),
            record.get_days_overdue(),
            f"{record.fine_amount:.2f}",
            'Yes' if record.fine_paid else 'No'
        ])
    
    return response


@login_required
@admin_required
def export_overdue_pdf(request):
    """Export overdue books to PDF"""
    from django.http import HttpResponse
    from .utils import generate_overdue_report_pdf
    
    pdf_buffer = generate_overdue_report_pdf()
    
    response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="overdue_report.pdf"'
    
    return response


@login_required
@admin_required
def export_fine_report_pdf(request):
    """Export fine report to PDF"""
    from django.http import HttpResponse
    from .utils import generate_fine_report_pdf
    
    pdf_buffer = generate_fine_report_pdf()
    
    response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="fine_report.pdf"'
    
    return response


@login_required
@admin_required
def export_top_books_pdf(request):
    """Export top 10 books report to PDF"""
    from django.http import HttpResponse
    from .utils import generate_top_books_report_pdf
    
    pdf_buffer = generate_top_books_report_pdf()
    
    response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="top_books_report.pdf"'
    
    return response


@login_required
@admin_required
def export_top_members_pdf(request):
    """Export top 10 members report to PDF"""
    from django.http import HttpResponse
    from .utils import generate_top_members_report_pdf
    
    pdf_buffer = generate_top_members_report_pdf()
    
    response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="top_members_report.pdf"'
    
    return response


@login_required
@admin_required
def create_backup(request):
    """
    Create a database backup and stream it directly to the browser.
    """
    from django.contrib import messages
    from django.http import HttpResponse
    from .utils import create_database_backup, log_activity

    try:
        buffer, fmt = create_database_backup()
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')

        if fmt == 'sqlite3':
            filename = f'db_backup_{timestamp}.sqlite3'
            content_type = 'application/octet-stream'
        elif fmt == 'sql':
            filename = f'db_backup_{timestamp}.sql'
            content_type = 'application/sql'
        else:
            filename = f'db_backup_{timestamp}.json'
            content_type = 'application/json'

        response = HttpResponse(buffer.read(), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        log_activity(request.user, 'backup_created', f'Database backup downloaded: {filename}', request)
        return response

    except Exception as e:
        messages.error(request, f'Failed to create backup: {str(e)}')
        return redirect('dashboard:system_admin')


@login_required
@admin_required
def restore_backup(request):
    """
    Restore database from an uploaded .sqlite3, .json, or .sql backup file.
    """
    from django.contrib import messages
    from .utils import log_activity

    if request.method == 'POST':
        uploaded_file = request.FILES.get('backup_file')

        if not uploaded_file:
            messages.error(request, 'Please upload a backup file (.sqlite3, .json, or .sql).')
            return redirect('dashboard:system_admin')

        filename = uploaded_file.name.lower()

        # ── SQLite restore ────────────────────────────────────────────────
        if filename.endswith('.sqlite3') or filename.endswith('.db'):
            try:
                import os
                from django.conf import settings as django_settings
                from django.db import connections

                db_path = str(django_settings.DATABASES['default'].get('NAME', ''))
                if not db_path or 'sqlite3' not in django_settings.DATABASES['default'].get('ENGINE', ''):
                    messages.error(request, 'Current database is not SQLite. Cannot restore a .sqlite3 file.')
                    return redirect('dashboard:system_admin')

                # Close all Django DB connections before replacing the file
                connections.close_all()

                with open(db_path, 'wb') as f:
                    for chunk in uploaded_file.chunks():
                        f.write(chunk)

                messages.success(request, 'Database restored successfully from SQLite backup.')
                log_activity(request.user, 'backup_restored', f'Database restored from SQLite: {uploaded_file.name}', request)

            except Exception as e:
                messages.error(request, f'Failed to restore SQLite backup: {str(e)}')

        # ── JSON restore (Django dumpdata) ────────────────────────────────
        elif filename.endswith('.json'):
            try:
                import tempfile, os
                from django.core.management import call_command

                with tempfile.NamedTemporaryFile(mode='wb', suffix='.json', delete=False) as tmp:
                    for chunk in uploaded_file.chunks():
                        tmp.write(chunk)
                    tmp_path = tmp.name

                call_command('loaddata', tmp_path, verbosity=0)
                os.unlink(tmp_path)

                messages.success(request, 'Database restored successfully from JSON backup.')
                log_activity(request.user, 'backup_restored', f'Database restored from JSON: {uploaded_file.name}', request)

            except Exception as e:
                messages.error(request, f'Failed to restore from JSON: {str(e)}')

        # ── SQL restore (PostgreSQL pg_dump) ──────────────────────────────
        elif filename.endswith('.sql'):
            try:
                import subprocess, os, tempfile
                from django.conf import settings as django_settings

                db = django_settings.DATABASES['default']
                database_url = os.environ.get('DATABASE_URL')

                with tempfile.NamedTemporaryFile(mode='wb', suffix='.sql', delete=False) as tmp:
                    for chunk in uploaded_file.chunks():
                        tmp.write(chunk)
                    tmp_path = tmp.name

                env = os.environ.copy()
                if database_url:
                    cmd = ['psql', database_url, '-f', tmp_path]
                else:
                    env['PGPASSWORD'] = db.get('PASSWORD', '')
                    cmd = [
                        'psql',
                        '-h', db.get('HOST', 'localhost'),
                        '-p', str(db.get('PORT', '5432')),
                        '-U', db.get('USER', ''),
                        '-d', db.get('NAME', ''),
                        '-f', tmp_path,
                    ]

                result = subprocess.run(cmd, env=env, capture_output=True, timeout=120)
                os.unlink(tmp_path)

                if result.returncode == 0:
                    messages.success(request, 'Database restored successfully from SQL backup.')
                    log_activity(request.user, 'backup_restored', f'Database restored from SQL: {uploaded_file.name}', request)
                else:
                    messages.error(request, f'psql restore failed: {result.stderr.decode()[:500]}')

            except FileNotFoundError:
                messages.error(request, 'psql command not found. Use a .sqlite3 or .json backup instead.')
            except Exception as e:
                messages.error(request, f'Failed to restore from SQL: {str(e)}')

        else:
            messages.error(request, 'Invalid file type. Please upload a .sqlite3, .json, or .sql backup file.')

    return redirect('dashboard:system_admin')


@login_required
@admin_required
def download_backup(request, backup_file):
    """
    Download backup is now handled by create_backup which streams directly.
    This endpoint is kept for URL compatibility but redirects to create_backup.
    """
    messages.info(request, 'Use the "Download Backup" button to generate and download a fresh backup.')
    return redirect('dashboard:system_admin')


@login_required
@admin_required
def upload_backup(request):
    """
    Upload a backup file and restore it immediately.
    Accepts .json (Django dumpdata) or .sql (pg_dump) files.
    No local storage — file is processed in memory and discarded.
    """
    from django.contrib import messages

    if request.method == 'POST':
        # Delegate to restore_backup which handles the actual restore
        return restore_backup(request)

    return redirect('dashboard:system_admin')


@login_required
@admin_required
def delete_backup(request, backup_file):
    """
    Backup files are not stored on disk — generated on demand.
    This endpoint is kept for URL compatibility.
    """
    messages.info(request, 'Backups are downloaded directly — no stored backups to delete.')
    return redirect('dashboard:system_admin')


@login_required
@admin_required
def send_due_reminders(request):
    """Send due date reminder emails"""
    from django.contrib import messages
    from .utils import send_due_reminder_emails, log_activity
    
    try:
        sent_count = send_due_reminder_emails()
        messages.success(request, f'Sent {sent_count} reminder email(s) successfully.')
        log_activity(request.user, 'reminder_sent', f'Sent {sent_count} due date reminder emails', request)
    except Exception as e:
        messages.error(request, f'Failed to send reminders: {str(e)}')
    
    return redirect('dashboard:system_admin')


@login_required
@admin_required
def send_overdue_notifications(request):
    """Send overdue notification emails"""
    from django.contrib import messages
    from .utils import send_overdue_notification_emails, log_activity
    
    try:
        sent_count = send_overdue_notification_emails()
        messages.success(request, f'Sent {sent_count} overdue notification(s) successfully.')
        log_activity(request.user, 'reminder_sent', f'Sent {sent_count} overdue notifications', request)
    except Exception as e:
        messages.error(request, f'Failed to send notifications: {str(e)}')
    
    return redirect('dashboard:system_admin')


@login_required
@admin_required
def activity_log_view(request):
    """View full activity log"""
    from django.core.paginator import Paginator
    from ..users.models import ActivityLog
    
    # Get all activity logs
    logs = ActivityLog.objects.select_related('user').all()
    
    # Filter by action type
    action_filter = request.GET.get('action', '')
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    # Filter by user
    user_filter = request.GET.get('user', '')
    if user_filter:
        logs = logs.filter(user__username__icontains=user_filter)
    
    # Filter by date range
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        logs = logs.filter(created_at__date__gte=date_from)
    if date_to:
        logs = logs.filter(created_at__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get action choices for filter
    from ..users.models import ActivityLog as AL
    action_choices = AL.ACTION_CHOICES
    
    context = {
        'page_obj': page_obj,
        'logs': page_obj.object_list,
        'action_filter': action_filter,
        'user_filter': user_filter,
        'date_from': date_from,
        'date_to': date_to,
        'action_choices': action_choices,
        'total_count': logs.count(),
    }
    
    return render(request, 'dashboard/activity_log.html', context)


@login_required
@librarian_or_admin_required
def reservation_management(request):
    """Manage book reservations/requests"""
    from ..borrow.models import BookRequest
    from django.db.models import Q
    
    # Get all requests with filters
    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    requests = BookRequest.objects.select_related('user', 'book', 'approved_by').all()
    
    if status_filter:
        requests = requests.filter(status=status_filter)
    
    if search:
        requests = requests.filter(
            Q(user__username__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(book__title__icontains=search)
        )
    
    # Get counts by status
    pending_count = BookRequest.objects.filter(status='pending').count()
    ready_count = BookRequest.objects.filter(status='ready').count()
    fulfilled_count = BookRequest.objects.filter(status='fulfilled').count()
    cancelled_count = BookRequest.objects.filter(status='cancelled').count()
    rejected_count = BookRequest.objects.filter(status='rejected').count()
    
    context = {
        'requests': requests,
        'status_filter': status_filter,
        'search': search,
        'pending_count': pending_count,
        'ready_count': ready_count,
        'fulfilled_count': fulfilled_count,
        'cancelled_count': cancelled_count,
        'rejected_count': rejected_count,
    }
    
    return render(request, 'dashboard/reservation_management.html', context)


@login_required
@admin_required
def system_administration(request):
    """System administration panel"""
    from ..users.models import ActivityLog
    from ..borrow.models import BorrowRecord
    from .models import SystemSettings
    from django.db.models import Sum
    import os
    
    # Get system settings
    system_settings = SystemSettings.get_settings()
    
    # Get system statistics
    total_logs = ActivityLog.objects.count()
    recent_logs = ActivityLog.objects.select_related('user').order_by('-created_at')[:10]
    
    # Backup info — backups are generated on-demand via "Download Backup"
    backups = []  # No stored backups — use "Download Backup" to get a fresh one
    
    # Get email statistics
    books_due_soon = BorrowRecord.objects.filter(
        status='borrowed',
        due_date__lte=timezone.now().date() + timedelta(days=3),
        due_date__gte=timezone.now().date()
    ).count()
    
    overdue_books = BorrowRecord.objects.filter(status='overdue').count()
    
    context = {
        'system_settings': system_settings,
        'total_logs': total_logs,
        'recent_logs': recent_logs,
        'backups': backups,
        'books_due_soon': books_due_soon,
        'overdue_books': overdue_books,
    }
    
    return render(request, 'dashboard/system_administration.html', context)


@login_required
@admin_required
def update_system_settings(request):
    """Update system-wide settings"""
    from .models import SystemSettings
    from django.contrib import messages
    
    if request.method == 'POST':
        settings_obj = SystemSettings.get_settings()
        
        try:
            # Get form data
            default_borrow_limit = int(request.POST.get('default_borrow_limit', 5))
            fine_per_day = float(request.POST.get('fine_per_day', 2.00))
            max_borrow_days = int(request.POST.get('max_borrow_days', 14))
            apply_to_all = request.POST.get('apply_to_all') == 'on'
            
            # Validate
            if not (1 <= default_borrow_limit <= 20):
                messages.error(request, 'Borrow limit must be between 1 and 20.')
                return redirect('dashboard:system_admin')
            
            if fine_per_day < 0:
                messages.error(request, 'Fine per day cannot be negative.')
                return redirect('dashboard:system_admin')
            
            if not (1 <= max_borrow_days <= 90):
                messages.error(request, 'Max borrow days must be between 1 and 90.')
                return redirect('dashboard:system_admin')
            
            # Update settings
            settings_obj.default_borrow_limit = default_borrow_limit
            settings_obj.fine_per_day = fine_per_day
            settings_obj.max_borrow_days = max_borrow_days
            settings_obj.updated_by = request.user
            settings_obj.save()
            
            # Apply to all users if requested
            if apply_to_all:
                from ..users.models import UserProfile
                updated_count = UserProfile.objects.all().update(max_books_allowed=default_borrow_limit)
                messages.success(request, f'System settings updated! Borrow limit of {default_borrow_limit} books applied to {updated_count} users.')
            else:
                messages.success(request, f'System settings updated! New users will have a borrow limit of {default_borrow_limit} books.')
            
        except (ValueError, TypeError) as e:
            messages.error(request, f'Invalid input: {str(e)}')
    
    return redirect('dashboard:system_admin')



@login_required
@admin_required
def system_settings_view(request):
    """View and edit system settings - Admin only"""
    from apps.dashboard.models import SystemSettings
    from django.contrib import messages
    
    settings = SystemSettings.get_settings()
    
    if request.method == 'POST':
        try:
            # Update settings from form
            settings.default_borrow_limit = int(request.POST.get('default_borrow_limit', 5))
            settings.fine_per_day = float(request.POST.get('fine_per_day', 2.00))
            settings.etb_to_usd_rate = float(request.POST.get('etb_to_usd_rate', 0.0180))
            settings.max_borrow_days = int(request.POST.get('max_borrow_days', 14))
            settings.updated_by = request.user
            settings.save()
            
            messages.success(request, 'System settings updated successfully!')
            
            # Log activity
            from .utils import log_activity
            log_activity(request.user, 'settings_updated', 'System settings updated', request)
            
        except Exception as e:
            messages.error(request, f'Error updating settings: {str(e)}')
    
    context = {
        'settings': settings,
    }
    
    return render(request, 'dashboard/system_settings.html', context)


@login_required
@librarian_or_admin_required
def notification_center(request):
    """
    Notification Center — send emails manually: bulk, individual,
    due-date alerts, overdue reminders, unpaid fine notices.
    Visible to both admin and librarian.
    """
    from apps.dashboard.models import SystemSettings
    from apps.users.notifications import _send_email_async
    from django.conf import settings as django_settings
    from django.template.loader import render_to_string
    import threading

    today = timezone.now().date()
    system_settings = SystemSettings.get_settings()
    fine_per_day = system_settings.fine_per_day

    # ── Data for the page sections ──────────────────────────────────────────
    # Due soon (within 3 days)
    due_soon_records = BorrowRecord.objects.filter(
        status='borrowed',
        due_date__lte=today + timedelta(days=3),
        due_date__gte=today,
    ).select_related('user', 'book').order_by('due_date')

    # Overdue
    overdue_records = BorrowRecord.objects.filter(
        status='overdue',
    ).select_related('user', 'book').order_by('due_date')

    # Unpaid fines
    unpaid_records = BorrowRecord.objects.filter(
        fine_amount__gt=0,
        fine_paid=False,
    ).select_related('user', 'book').order_by('-fine_amount')

    # All active users (for individual / bulk custom email)
    all_users = User.objects.filter(is_active=True).order_by('first_name', 'username')

    # ── Handle POST actions ─────────────────────────────────────────────────
    if request.method == 'POST':
        action = request.POST.get('action', '')

        # Helper: send one email via the existing async helper
        def _queue(subject, user_obj, text, html):
            if user_obj.email:
                _send_email_async(
                    subject, text, html,
                    django_settings.DEFAULT_FROM_EMAIL,
                    user_obj.email,
                    require_verified=False,   # staff-initiated — trust the address
                )

        # ── 1. Send due-soon reminders ──────────────────────────────────────
        if action == 'send_due_soon':
            record_ids = request.POST.getlist('record_ids')
            qs = due_soon_records
            if record_ids:
                qs = qs.filter(id__in=record_ids)

            sent = 0
            for rec in qs:
                days_left = (rec.due_date - today).days
                ctx = {
                    'user': rec.user, 'book': rec.book,
                    'due_date': rec.due_date, 'days_remaining': days_left,
                    'fine_per_day': fine_per_day,
                    'site_name': django_settings.SITE_NAME,
                    'site_url': django_settings.SITE_URL,
                }
                subject = f'Reminder: "{rec.book.title}" due in {days_left} day(s)'
                _queue(subject, rec.user,
                       render_to_string('emails/book_due_soon.txt', ctx),
                       render_to_string('emails/book_due_soon.html', ctx))
                sent += 1

            from apps.dashboard.utils import log_activity
            log_activity(request.user, 'reminder_sent',
                         f'Sent {sent} due-soon reminder(s) from Notification Center', request)
            messages.success(request, f'Sent {sent} due-date reminder email(s).')
            return redirect('dashboard:notification_center')

        # ── 2. Send overdue notifications ───────────────────────────────────
        elif action == 'send_overdue':
            record_ids = request.POST.getlist('record_ids')
            qs = overdue_records
            if record_ids:
                qs = qs.filter(id__in=record_ids)

            sent = 0
            for rec in qs:
                days_over = (today - rec.due_date).days
                current_fine = days_over * fine_per_day
                ctx = {
                    'user': rec.user, 'book': rec.book,
                    'due_date': rec.due_date, 'days_overdue': days_over,
                    'fine_amount': current_fine, 'fine_per_day': fine_per_day,
                    'site_name': django_settings.SITE_NAME,
                    'site_url': django_settings.SITE_URL,
                }
                subject = f'OVERDUE: "{rec.book.title}" — {days_over} day(s) late'
                _queue(subject, rec.user,
                       render_to_string('emails/book_overdue.txt', ctx),
                       render_to_string('emails/book_overdue.html', ctx))
                sent += 1

            from apps.dashboard.utils import log_activity
            log_activity(request.user, 'reminder_sent',
                         f'Sent {sent} overdue notification(s) from Notification Center', request)
            messages.success(request, f'Sent {sent} overdue notification email(s).')
            return redirect('dashboard:notification_center')

        # ── 3. Send unpaid fine notices ─────────────────────────────────────
        elif action == 'send_unpaid':
            record_ids = request.POST.getlist('record_ids')
            qs = unpaid_records
            if record_ids:
                qs = qs.filter(id__in=record_ids)

            sent = 0
            for rec in qs:
                days_over = max((today - rec.due_date).days, 0)
                ctx = {
                    'user': rec.user, 'book': rec.book,
                    'due_date': rec.due_date, 'days_overdue': days_over,
                    'fine_amount': rec.fine_amount, 'fine_per_day': fine_per_day,
                    'site_name': django_settings.SITE_NAME,
                    'site_url': django_settings.SITE_URL,
                }
                subject = f'Unpaid Fine: ETB {rec.fine_amount} for "{rec.book.title}"'
                _queue(subject, rec.user,
                       render_to_string('emails/fine_applied.txt', ctx),
                       render_to_string('emails/fine_applied.html', ctx))
                sent += 1

            from apps.dashboard.utils import log_activity
            log_activity(request.user, 'reminder_sent',
                         f'Sent {sent} unpaid-fine notice(s) from Notification Center', request)
            messages.success(request, f'Sent {sent} unpaid fine notice email(s).')
            return redirect('dashboard:notification_center')

        # ── 4. Custom bulk / individual email ───────────────────────────────
        elif action == 'send_custom':
            subject = request.POST.get('subject', '').strip()
            body = request.POST.get('body', '').strip()
            recipient_type = request.POST.get('recipient_type', 'all')
            selected_ids = request.POST.getlist('selected_user_ids')

            if not subject or not body:
                messages.error(request, 'Subject and message body are required.')
                return redirect('dashboard:notification_center')

            if recipient_type == 'all':
                recipients = User.objects.filter(is_active=True)
            elif recipient_type == 'students':
                recipients = User.objects.filter(role='student', is_active=True)
            elif recipient_type == 'librarians':
                recipients = User.objects.filter(role='librarian', is_active=True)
            elif recipient_type == 'specific':
                if not selected_ids:
                    messages.error(request, 'Please select at least one user.')
                    return redirect('dashboard:notification_center')
                recipients = User.objects.filter(id__in=selected_ids, is_active=True)
            else:
                recipients = User.objects.filter(is_active=True)

            sent = 0
            for u in recipients:
                if not u.email:
                    continue
                personalised_body = (
                    body
                    .replace('{name}', u.get_full_name() or u.username)
                    .replace('{username}', u.username)
                    .replace('{email}', u.email)
                )
                html_body = personalised_body.replace('\n', '<br>')
                html = f"""
                <html><body style="font-family:Inter,sans-serif;color:#1f2937;line-height:1.6;">
                <p>{html_body}</p>
                <hr style="margin:24px 0;border:none;border-top:1px solid #e5e7eb;">
                <p style="font-size:0.8125rem;color:#9ca3af;">
                    SmartLibrary &mdash; {django_settings.SITE_URL}
                </p></body></html>"""
                _send_email_async(
                    subject, personalised_body, html,
                    django_settings.DEFAULT_FROM_EMAIL, u.email,
                    require_verified=False,
                )
                sent += 1

            from apps.dashboard.utils import log_activity
            log_activity(request.user, 'other',
                         f'Sent custom email to {sent} user(s): "{subject}"', request)
            messages.success(request, f'Sent custom email to {sent} user(s).')
            return redirect('dashboard:notification_center')

    # ── Summary counts for the page ─────────────────────────────────────────
    from django.db.models import Sum as DSum
    total_unpaid_amount = unpaid_records.aggregate(t=DSum('fine_amount'))['t'] or 0

    context = {
        'due_soon_records': due_soon_records,
        'overdue_records': overdue_records,
        'unpaid_records': unpaid_records,
        'all_users': all_users,
        'due_soon_count': due_soon_records.count(),
        'overdue_count': overdue_records.count(),
        'unpaid_count': unpaid_records.count(),
        'total_unpaid_amount': total_unpaid_amount,
        'fine_per_day': fine_per_day,
        'today': today,
    }
    return render(request, 'dashboard/notification_center.html', context)

