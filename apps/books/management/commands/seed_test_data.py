"""
Comprehensive test data seed command.
Creates rich data for ezedin (presentation account) + supporting users.

Usage:
    python manage.py seed_test_data
    python manage.py seed_test_data --clear   # wipe existing test data first

Ezedin's data layout (for presentation):
  - 17 books currently borrowed (active, within due date)
  -  3 books currently overdue  (active, past due date, fine accumulating)
  -  5 books returned ON TIME   (no fine)
  -  7 books returned LATE with UNPAID fine (need payment - pending)
  -  5 books returned LATE with PAID fine   (payment completed)
  Total active borrows: 20 | Total returned: 17 | Grand total: 37 records

  - Book requests: 3 pending, 1 ready/approved, 2 rejected, 1 cancelled, 1 fulfilled
  - Reviews: for 6 returned books (mix of ratings)
  - Payments: 7 pending + 5 completed
"""
import uuid
from io import BytesIO
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.books.models import Book, Category, BookReview
from apps.borrow.models import BorrowRecord, BookRequest
from apps.payments.models import Payment, StripePayment, ChapaPayment
from apps.users.models import UserProfile
from apps.dashboard.models import SystemSettings

User = get_user_model()
PASSWORD = 'Pass@123'


class Command(BaseCommand):
    help = 'Seed comprehensive test data for presentation (ezedin + supporting users)'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true',
                            help='Delete existing test data before seeding')

    def handle(self, *args, **options):
        if options['clear']:
            self._clear_test_data()

        self.stdout.write(self.style.MIGRATE_HEADING('\n' + '='*60))
        self.stdout.write(self.style.MIGRATE_HEADING('  SEEDING PRESENTATION TEST DATA'))
        self.stdout.write(self.style.MIGRATE_HEADING('='*60))

        with transaction.atomic():
            self._seed_system_settings()
            support_users = self._seed_support_users()
            books = self._load_real_books()
            self._seed_ezedin(books, support_users)
            self._seed_support_data(support_users, books)

        self.stdout.write(self.style.MIGRATE_HEADING('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('  ALL TEST DATA SEEDED SUCCESSFULLY'))
        self.stdout.write(self.style.MIGRATE_HEADING('='*60))
        self.stdout.write('\nPresentation account:')
        self.stdout.write('  Student  : ezedinnmoh@gmail.com  (main demo account)')
        self.stdout.write('\nSupport test accounts (password: Pass@123):')
        self.stdout.write('  Admin    : admin_test / admin_test@library.com')
        self.stdout.write('  Librarian: lib_test   / lib_test@library.com')
        self.stdout.write('  Student  : stu_test1  / stu_test1@library.com')
        self.stdout.write('  Student  : stu_test2  / stu_test2@library.com')
        self.stdout.write('  Student  : stu_test3  / stu_test3@library.com')
        self.stdout.write('  Student  : stu_test4  / stu_test4@library.com')
        self.stdout.write('  Student  : stu_test5  / stu_test5@library.com\n')

    # ── Clear ────────────────────────────────────────────────────────────────
    def _clear_test_data(self):
        self.stdout.write(self.style.WARNING('\nClearing existing test data...'))

        # Clear support test users
        test_usernames = [
            'admin_test', 'lib_test',
            'stu_test1', 'stu_test2', 'stu_test3', 'stu_test4', 'stu_test5'
        ]
        deleted = User.objects.filter(username__in=test_usernames).delete()
        self.stdout.write(self.style.WARNING(f'  Deleted test users: {deleted[0]} objects'))

        # Clear ezedin's data WITHOUT deleting the account
        ezedin = User.objects.filter(email='ezedinnmoh@gmail.com').first()
        if ezedin:
            BorrowRecord.objects.filter(user=ezedin).delete()
            BookRequest.objects.filter(user=ezedin).delete()
            Payment.objects.filter(user=ezedin).delete()
            BookReview.objects.filter(user=ezedin).delete()
            # Reset profile
            profile, _ = UserProfile.objects.get_or_create(user=ezedin)
            profile.currently_borrowed = 0
            profile.total_books_read = 0
            profile.total_fines = Decimal('0.00')
            profile.max_books_allowed = 30
            profile.save()
            self.stdout.write(self.style.WARNING(
                f'  Cleared data for {ezedin.username} ({ezedin.email})'
            ))

    # ── System Settings ──────────────────────────────────────────────────────
    def _seed_system_settings(self):
        s = SystemSettings.get_settings()
        s.fine_per_day = Decimal('2.00')
        s.max_borrow_days = 14
        s.default_borrow_limit = 7
        s.etb_to_usd_rate = Decimal('0.0180')
        s.save()
        self.stdout.write(self.style.SUCCESS('[OK] System settings configured'))

    # ── Support Users ────────────────────────────────────────────────────────
    def _seed_support_users(self):
        self.stdout.write('\nCreating support users...')
        users = {}
        specs = [
            ('admin_test',  'admin_test@library.com',  'admin',     'Admin',   'Test'),
            ('lib_test',    'lib_test@library.com',    'librarian', 'Lib',     'Test'),
            ('stu_test1',   'stu_test1@library.com',   'student',   'Alice',   'Student'),
            ('stu_test2',   'stu_test2@library.com',   'student',   'Bob',     'Student'),
            ('stu_test3',   'stu_test3@library.com',   'student',   'Carol',   'Student'),
            ('stu_test4',   'stu_test4@library.com',   'student',   'David',   'Student'),
            ('stu_test5',   'stu_test5@library.com',   'student',   'Eve',     'Student'),
        ]
        for username, email, role, first, last in specs:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email, 'role': role,
                    'first_name': first, 'last_name': last, 'is_active': True,
                }
            )
            user.set_password(PASSWORD)
            user.is_active = True
            user.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.max_books_allowed = 7
            profile.save()
            users[username] = user
            tag = '[OK] Created' if created else '  ~ Exists '
            self.stdout.write(self.style.SUCCESS(f'  {tag}: {username}'))
        return users

    # ── Load Real Books ───────────────────────────────────────────────────────
    def _load_real_books(self):
        self.stdout.write('\nLoading real books from database...')

        # Priority 1: books with BOTH cover image and PDF
        priority1 = list(
            Book.objects.exclude(cover_image='').exclude(cover_image__isnull=True)
                        .exclude(pdf_file='').exclude(pdf_file__isnull=True)
                        .order_by('id')
        )
        self.stdout.write(f'  Books with cover+pdf : {len(priority1)}')

        # Priority 2: books with cover image only
        p1_ids = [b.id for b in priority1]
        priority2 = list(
            Book.objects.exclude(cover_image='').exclude(cover_image__isnull=True)
                        .exclude(id__in=p1_ids)
                        .order_by('id')
        )
        self.stdout.write(f'  Books with cover only: {len(priority2)}')

        # Priority 3: any remaining books
        p12_ids = p1_ids + [b.id for b in priority2]
        priority3 = list(Book.objects.exclude(id__in=p12_ids).order_by('id'))
        self.stdout.write(f'  Other books          : {len(priority3)}')

        all_books = priority1 + priority2 + priority3
        self.stdout.write(self.style.SUCCESS(
            f'[OK] {len(all_books)} books available (prioritising cover+pdf)'
        ))

        if len(all_books) < 10:
            raise Exception('Not enough books in database! Please add books first.')

        return all_books

    # ── EZEDIN Main Demo Account ──────────────────────────────────────────────
    def _seed_ezedin(self, books, support_users):
        ezedin = User.objects.filter(email='ezedinnmoh@gmail.com').first()
        if not ezedin:
            self.stdout.write(self.style.WARNING(
                '\n[!] User ezedinnmoh@gmail.com not found — skipping ezedin data.'
            ))
            return

        self.stdout.write(f'\nSeeding data for {ezedin.username} ({ezedin.email})...')

        # Ensure profile allows 30 active borrows
        profile, _ = UserProfile.objects.get_or_create(user=ezedin)
        profile.max_books_allowed = 30
        profile.currently_borrowed = 0
        profile.total_books_read = 0
        profile.save()

        lib = support_users['lib_test']
        book_idx = 0  # global index into the books list

        def next_book(n=1):
            nonlocal book_idx
            result = []
            for _ in range(n):
                result.append(books[book_idx % len(books)])
                book_idx += 1
            return result if n > 1 else result[0]

        # ── 1. 17 ACTIVE BORROWS (within due date) ────────────────────────────
        self.stdout.write('  [1/7] Creating 17 active borrows (within due date)...')
        active_scenarios = [
            # (days_ago_borrowed, days_until_due)
            (1,  13), (2,  12), (3,  11), (4,  10), (5,   9),
            (6,   8), (7,   7), (8,   6), (9,   5), (10,  4),
            (11,  3), (12,  2), (13,  1), (1,  13), (3,  11),
            (5,   9), (7,   7),
        ]
        for days_ago, days_left in active_scenarios:
            self._create_borrow(
                user=ezedin, book=next_book(), status='borrowed',
                days_ago=days_ago, due_in=days_left, issued_by=lib
            )

        # ── 2. 3 OVERDUE BORROWS (past due date, fine accumulating) ───────────
        self.stdout.write('  [2/7] Creating 3 overdue borrows (fine accumulating)...')
        overdue_scenarios = [
            # (days_borrowed_ago, days_past_due, fine)
            (18,  -4,  8.00),   # 4 days overdue = ETB 8
            (22,  -8, 16.00),   # 8 days overdue = ETB 16
            (30, -16, 32.00),   # 16 days overdue = ETB 32
        ]
        for days_ago, due_in, fine in overdue_scenarios:
            self._create_borrow(
                user=ezedin, book=next_book(), status='overdue',
                days_ago=days_ago, due_in=due_in, fine=fine, fine_paid=False,
                issued_by=lib
            )

        # ── 3. 5 RETURNED ON TIME (no fine) ──────────────────────────────────
        self.stdout.write('  [3/7] Creating 5 returned-on-time borrows (no fine)...')
        on_time_scenarios = [
            # (days_borrowed_ago, return_days_ago, note)
            (30, 20, 'returned 10 days before due'),
            (45, 33, 'returned 2 days before due'),
            (60, 50, 'returned 4 days before due'),
            (90, 78, 'returned 2 days before due'),
            (20, 12, 'returned 6 days before due'),
        ]
        for days_ago, returned_days_ago, _ in on_time_scenarios:
            # due_in is positive => return was before due date
            self._create_borrow(
                user=ezedin, book=next_book(), status='returned',
                days_ago=days_ago, due_in=-(days_ago - returned_days_ago - 14),
                returned_days_ago=returned_days_ago, fine=0, fine_paid=False,
                issued_by=lib, returned_to=lib
            )

        # ── 4. 7 RETURNED LATE with UNPAID FINE (need payment) ────────────────
        self.stdout.write('  [4/7] Creating 7 returned-late / unpaid-fine borrows...')
        unpaid_scenarios = [
            # (days_borrowed_ago, returned_days_ago, fine_amount)
            (40, 10, 10.00),   # 5 days late
            (50, 15,  8.00),   # 4 days late
            (55, 20, 14.00),   # 7 days late
            (65, 25, 12.00),   # 6 days late
            (70, 30, 18.00),   # 9 days late
            (80, 35, 20.00),   # 10 days late
            (90, 40, 16.00),   # 8 days late
        ]
        unpaid_borrow_records = []
        for days_ago, returned_days_ago, fine in unpaid_scenarios:
            rec = self._create_borrow(
                user=ezedin, book=next_book(), status='returned',
                days_ago=days_ago, due_in=-(days_ago - returned_days_ago - 14),
                returned_days_ago=returned_days_ago,
                fine=fine, fine_paid=False,
                issued_by=lib, returned_to=lib
            )
            if rec:
                unpaid_borrow_records.append((rec, fine))

        # Create PENDING payments for these
        self.stdout.write('      Creating pending payments for unpaid fines...')
        for rec, fine in unpaid_borrow_records:
            self._create_payment(ezedin, rec, fine, method='chapa', status='pending')

        # ── 5. 5 RETURNED LATE with PAID FINE ────────────────────────────────
        self.stdout.write('  [5/7] Creating 5 returned-late / paid-fine borrows...')
        paid_scenarios = [
            # (days_borrowed_ago, returned_days_ago, fine_amount, method)
            (100, 50, 22.00, 'chapa'),
            (110, 60, 10.00, 'stripe'),
            (120, 65, 16.00, 'chapa'),
            (130, 75, 18.00, 'stripe'),
            (150, 90, 24.00, 'chapa'),
        ]
        paid_borrow_records = []
        for days_ago, returned_days_ago, fine, method in paid_scenarios:
            rec = self._create_borrow(
                user=ezedin, book=next_book(), status='returned',
                days_ago=days_ago, due_in=-(days_ago - returned_days_ago - 14),
                returned_days_ago=returned_days_ago,
                fine=fine, fine_paid=True,
                issued_by=lib, returned_to=lib
            )
            if rec:
                paid_borrow_records.append((rec, fine, method))

        # Create COMPLETED payments for these
        self.stdout.write('      Creating completed payments for paid fines...')
        for rec, fine, method in paid_borrow_records:
            self._create_payment(ezedin, rec, fine, method=method, status='completed')

        # ── 6. BOOK REQUESTS ─────────────────────────────────────────────────
        self.stdout.write('  [6/7] Creating book requests...')
        lib_user = support_users['lib_test']
        req_books = books[book_idx % len(books):]  # remaining books for requests
        if len(req_books) < 8:
            req_books = books  # wrap around

        request_scenarios = [
            # (book_index, status, approved_by, rejection_reason, cancel_reason, days_ago)
            (0, 'pending',   None,      '',                                       '',                    1),
            (1, 'pending',   None,      '',                                       '',                    2),
            (2, 'pending',   None,      '',                                       '',                    3),
            (3, 'ready',     lib_user,  '',                                       '',                    5),  # approved, ready to pickup
            (4, 'rejected',  lib_user,  'Book is currently reserved for another student.', '', 7),
            (5, 'rejected',  lib_user,  'Maximum borrow limit reached at time of request.', '', 10),
            (6, 'cancelled', None,      '',                                       'No longer needed.',   4),
            (7, 'fulfilled', lib_user,  '',                                       '',                    15), # already converted to borrow
        ]
        for i, (b_idx, status, approved_by, rej_reason, cancel_reason, days_ago) in enumerate(request_scenarios):
            req_book = req_books[b_idx % len(req_books)]
            if BookRequest.objects.filter(user=ezedin, book=req_book).exists():
                continue
            req = BookRequest(
                user=ezedin,
                book=req_book,
                status=status,
                approved_by=approved_by,
                rejection_reason=rej_reason,
                cancellation_reason=cancel_reason,
                notes=f'Test request #{i+1} for presentation demo.',
            )
            if approved_by and status in ('ready', 'rejected', 'fulfilled'):
                req.approved_date = timezone.now() - timedelta(days=max(days_ago - 1, 1))
            BookRequest.objects.bulk_create([req])

        self.stdout.write(self.style.SUCCESS('      [OK] 8 book requests created'))

        # ── 7. REVIEWS ───────────────────────────────────────────────────────
        self.stdout.write('  [7/7] Creating book reviews...')
        # ezedin can review books they've returned (status='returned')
        returned_records = BorrowRecord.objects.filter(
            user=ezedin, status='returned'
        ).select_related('book').order_by('id')

        review_data = [
            (5, 'Absolutely outstanding! This book transformed my understanding of the subject completely.'),
            (4, 'Really well written and engaging. I learned a great deal. Highly recommend.'),
            (5, 'One of the best books I have ever read. The content is very practical and insightful.'),
            (3, 'Decent book, covers the basics well but could go deeper into advanced topics.'),
            (4, 'Very good read. Clear explanations and great examples throughout.'),
            (2, 'Not exactly what I expected. The writing style was a bit dry for my taste.'),
        ]

        review_count = 0
        for i, record in enumerate(returned_records[:6]):
            if BookReview.objects.filter(user=ezedin, book=record.book).exists():
                continue
            rating, text = review_data[i % len(review_data)]
            try:
                BookReview.objects.create(
                    user=ezedin,
                    book=record.book,
                    rating=rating,
                    review_text=text,
                )
                # Update book rating
                from django.db.models import Avg
                avg = record.book.reviews.aggregate(Avg('rating'))['rating__avg']
                if avg:
                    Book.objects.filter(pk=record.book.pk).update(rating=round(avg, 2))
                review_count += 1
            except Exception as e:
                self.stdout.write(f'      [!] Review skipped: {e}')

        self.stdout.write(self.style.SUCCESS(f'      [OK] {review_count} reviews created'))

        # ── Update ezedin profile stats ───────────────────────────────────────
        active_count = BorrowRecord.objects.filter(
            user=ezedin, status__in=['borrowed', 'overdue']
        ).count()
        returned_count = BorrowRecord.objects.filter(
            user=ezedin, status='returned'
        ).count()
        profile.currently_borrowed = active_count
        profile.total_books_read = returned_count
        if returned_count >= 20:
            profile.reading_badge = 'avid_reader'
        elif returned_count >= 10:
            profile.reading_badge = 'book_lover'
        else:
            profile.reading_badge = 'reader'
        profile.save()

        self.stdout.write(self.style.SUCCESS(
            f'\n[OK] Ezedin data complete:'
        ))
        self.stdout.write(f'     Active borrows : {active_count}  (17 on time + 3 overdue)')
        self.stdout.write(f'     Returned books : {returned_count}  (5 on time + 7 unpaid fine + 5 paid fine)')
        self.stdout.write(f'     Book requests  : 8  (3 pending, 1 ready, 2 rejected, 1 cancelled, 1 fulfilled)')
        self.stdout.write(f'     Reviews written: {review_count}')
        self.stdout.write(f'     Payments       : 7 pending + 5 completed')

    # ── Support Student Data (for admin pages) ────────────────────────────────
    def _seed_support_data(self, users, books):
        self.stdout.write('\nCreating support data for admin/librarian pages...')
        lib = users['lib_test']

        # stu_test1: 3 active borrows
        for i in range(3):
            self._create_borrow(users['stu_test1'], books[i % len(books)],
                                status='borrowed', days_ago=i+1, due_in=13-i,
                                issued_by=lib)
        # pending requests for stu_test1
        for i in range(3, 5):
            b = books[i % len(books)]
            if not BookRequest.objects.filter(user=users['stu_test1'], book=b).exists():
                BookRequest.objects.bulk_create([BookRequest(user=users['stu_test1'], book=b, status='pending')])

        # stu_test2: 1 overdue with unpaid fine
        rec2 = self._create_borrow(users['stu_test2'], books[5 % len(books)],
                                   status='overdue', days_ago=20, due_in=-6, fine=12.00,
                                   issued_by=lib)
        if rec2:
            self._create_payment(users['stu_test2'], rec2, 12.00, 'chapa', 'pending')
        # stu_test2: 2 returned on time
        for i in range(6, 8):
            self._create_borrow(users['stu_test2'], books[i % len(books)],
                                status='returned', days_ago=40, due_in=-(40-30-14),
                                returned_days_ago=30, fine=0, issued_by=lib, returned_to=lib)
        # stu_test2: pending request
        b2_req = books[8 % len(books)]
        if not BookRequest.objects.filter(user=users['stu_test2'], book=b2_req).exists():
            BookRequest.objects.bulk_create([BookRequest(user=users['stu_test2'], book=b2_req, status='pending')])

        # stu_test3: 2 returned, 1 active, 2 reviews
        self._create_borrow(users['stu_test3'], books[9 % len(books)],
                            status='returned', days_ago=30, due_in=-(30-20-14),
                            returned_days_ago=20, fine=0, issued_by=lib, returned_to=lib)
        self._create_borrow(users['stu_test3'], books[10 % len(books)],
                            status='returned', days_ago=60, due_in=-(60-46-14),
                            returned_days_ago=46, fine=0, issued_by=lib, returned_to=lib)
        self._create_borrow(users['stu_test3'], books[11 % len(books)],
                            status='borrowed', days_ago=2, due_in=12, issued_by=lib)

        for j, rec_book_idx in enumerate([9, 10]):
            b = books[rec_book_idx % len(books)]
            if not BookReview.objects.filter(user=users['stu_test3'], book=b).exists():
                try:
                    BookReview.objects.create(
                        user=users['stu_test3'], book=b,
                        rating=4+j, review_text='Great book for students!'
                    )
                except Exception:
                    pass

        # stu_test4: 1 overdue with PAID fine
        rec4 = self._create_borrow(users['stu_test4'], books[12 % len(books)],
                                   status='overdue', days_ago=25, due_in=-11,
                                   fine=22.00, fine_paid=True, issued_by=lib)
        if rec4:
            self._create_payment(users['stu_test4'], rec4, 22.00, 'stripe', 'completed')
        # stu_test4 rejected request
        b4_req = books[13 % len(books)]
        if not BookRequest.objects.filter(user=users['stu_test4'], book=b4_req).exists():
            BookRequest.objects.bulk_create([BookRequest(
                user=users['stu_test4'], book=b4_req, status='rejected',
                approved_by=lib, rejection_reason='Book unavailable this semester.',
                approved_date=timezone.now() - timedelta(days=2)
            )])

        # stu_test5: returned with unpaid fine + cancelled request
        rec5 = self._create_borrow(users['stu_test5'], books[14 % len(books)],
                                   status='returned', days_ago=40, due_in=-(40-26-14),
                                   returned_days_ago=26, fine=20.00, fine_paid=False,
                                   issued_by=lib, returned_to=lib)
        if rec5:
            self._create_payment(users['stu_test5'], rec5, 20.00, 'chapa', 'pending')
        b5_req = books[15 % len(books)]
        if not BookRequest.objects.filter(user=users['stu_test5'], book=b5_req).exists():
            BookRequest.objects.bulk_create([BookRequest(
                user=users['stu_test5'], book=b5_req, status='cancelled',
                cancellation_reason='Changed my mind.'
            )])

        # Update profile counts for all support students
        for key in ['stu_test1', 'stu_test2', 'stu_test3', 'stu_test4', 'stu_test5']:
            u = users[key]
            active = BorrowRecord.objects.filter(user=u, status__in=['borrowed', 'overdue']).count()
            returned = BorrowRecord.objects.filter(user=u, status='returned').count()
            UserProfile.objects.filter(user=u).update(
                currently_borrowed=active,
                total_books_read=returned
            )

        self.stdout.write(self.style.SUCCESS('[OK] Support student data created'))

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _create_borrow(self, user, book, status, days_ago, due_in,
                       fine=0, fine_paid=False, returned_days_ago=None,
                       issued_by=None, returned_to=None):
        """Create a BorrowRecord directly, bypassing model validation."""
        # Skip if exact duplicate already exists
        if BorrowRecord.objects.filter(
            user=user, book=book, status=status,
            fine_amount=Decimal(str(fine))
        ).exists():
            return None

        borrow_date = timezone.now() - timedelta(days=days_ago)
        due_date    = timezone.now().date() + timedelta(days=due_in)
        return_date = None
        if returned_days_ago is not None:
            return_date = timezone.now().date() - timedelta(days=returned_days_ago)

        record = BorrowRecord(
            user=user,
            book=book,
            borrow_date=borrow_date,
            due_date=due_date,
            return_date=return_date,
            status=status,
            fine_amount=Decimal(str(fine)),
            fine_paid=fine_paid,
            issued_by=issued_by,
            returned_to=returned_to,
        )
        BorrowRecord.objects.bulk_create([record])

        # Fetch the saved record so we have a PK
        saved = BorrowRecord.objects.filter(
            user=user, book=book, status=status,
            fine_amount=Decimal(str(fine))
        ).order_by('-id').first()

        # Update book availability counters
        if status in ('borrowed', 'overdue'):
            Book.objects.filter(pk=book.pk, available_copies__gt=0).update(
                available_copies=Book.objects.filter(pk=book.pk).values_list(
                    'available_copies', flat=True)[0] - 1,
                times_borrowed=Book.objects.filter(pk=book.pk).values_list(
                    'times_borrowed', flat=True)[0] + 1
            )
        elif status == 'returned':
            Book.objects.filter(pk=book.pk).update(
                times_borrowed=Book.objects.filter(pk=book.pk).values_list(
                    'times_borrowed', flat=True)[0] + 1
            )

        return saved

    def _create_payment(self, user, borrow_record, amount, method, status):
        """Create a Payment (and gateway detail) for a borrow record."""
        if borrow_record is None:
            return
        if Payment.objects.filter(borrow_record=borrow_record).exists():
            return

        currency = 'USD' if method == 'stripe' else 'ETB'
        tx_id = f'TEST-{method.upper()}-{uuid.uuid4().hex[:10].upper()}'

        payment = Payment.objects.create(
            user=user,
            borrow_record=borrow_record,
            amount=Decimal(str(amount)),
            currency=currency,
            payment_method=method,
            status=status,
            transaction_id=tx_id,
        )

        if method == 'stripe':
            StripePayment.objects.get_or_create(
                payment=payment,
                defaults={'stripe_payment_intent_id': f'pi_test_{uuid.uuid4().hex[:18]}'}
            )
        else:
            chapa_methods = ['telebirr', 'cbebirr', 'ebirr', 'mpesa', 'bank']
            chapa_method = chapa_methods[hash(tx_id) % len(chapa_methods)]
            ChapaPayment.objects.get_or_create(
                payment=payment,
                defaults={
                    'chapa_tx_ref': f'CHAPA-TEST-{uuid.uuid4().hex[:10].upper()}',
                    'payment_method_type': chapa_method,
                }
            )
