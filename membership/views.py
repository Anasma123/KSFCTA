from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from .models import MembershipApplication
from .forms import MembershipRegistrationForm
from .exports import (
    export_applications_to_excel,
    export_single_application_docx,
    export_letterhead_certificate_pdf,
    export_summary_pdf
)


from django.views.decorators.cache import never_cache

@never_cache
def home_view(request):
    """
    Public home page with online registration (including wings & ₹200 payment),
    direct portal login modal/section, and exact campaign contents.
    """
    form = MembershipRegistrationForm()
    login_error = None

    # Handle direct inline login from the homepage
    if request.method == 'POST' and 'action_login' in request.POST:
        user_input = request.POST.get('username_or_email', '').strip()
        pwd_input = request.POST.get('password', '').strip()

        # Try username or email
        user = authenticate(request, username=user_input, password=pwd_input)
        if user is None and '@' in user_input:
            try:
                user_obj = User.objects.get(email__iexact=user_input)
                user = authenticate(request, username=user_obj.username, password=pwd_input)
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                user = None

        if user is not None and user.is_active:
            login(request, user)
            if user.is_staff or user.is_superuser:
                return redirect('admin_portal')
            return redirect('member_dashboard')
        else:
            login_error = "Invalid email/username or password. Please verify your credentials."

    # Handle registration form submission
    elif request.method == 'POST':
        form = MembershipRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Create User account for applicant login
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=form.cleaned_data['full_name'][:30]
            )

            app = form.save(commit=False)
            app.user = user
            app.membership_fee = '₹ 200'
            app.save()

            # Auto log in the new member
            login(request, user)
            messages.success(request, f"Registration Successful! Welcome, {app.full_name}. Your Application No is {app.application_no}.")
            return redirect('registration_success', pk=app.id)

    registered_count = MembershipApplication.objects.count()
    context = {
        'form': form,
        'registered_count': registered_count,
        'login_error': login_error,
    }
    return render(request, 'membership/index.html', context)


def registration_success_view(request, pk):
    """Confirmation page with member slip and instant letterhead download / portal access."""
    app = get_object_or_404(MembershipApplication, pk=pk)
    return render(request, 'membership/success.html', {'app': app})


@never_cache
def login_view(request):
    """
    Direct login endpoint (accessible at /login/ or from the main page).
    Authenticates both Admin (shafi / shafi@pulpara) and Members (email / password).
    """
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('admin_portal')
        return redirect('member_dashboard')

    error_msg = None
    if request.method == 'POST':
        user_input = request.POST.get('username', '').strip()
        pwd_input = request.POST.get('password', '').strip()

        # Try username or email
        user = authenticate(request, username=user_input, password=pwd_input)
        if user is None and '@' in user_input:
            try:
                user_obj = User.objects.get(email__iexact=user_input)
                user = authenticate(request, username=user_obj.username, password=pwd_input)
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                user = None

        if user is not None and user.is_active:
            login(request, user)
            if user.is_staff or user.is_superuser:
                return redirect('admin_portal')
            return redirect('member_dashboard')
        else:
            error_msg = "Invalid credentials. Please verify your Email/Username and Password."

    return render(request, 'membership/login.html', {'error_msg': error_msg})


def logout_view(request):
    """Log out user and redirect to home."""
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('home')


@login_required(login_url='/login/')
def member_dashboard_view(request):
    """Teacher / Member Dashboard to view application status, payment verification, and download certificate."""
    try:
        app = request.user.application
    except Exception:
        # Fallback if matched by email
        app = MembershipApplication.objects.filter(email__iexact=request.user.email).first()

    if not app:
        messages.warning(request, "No membership application found for your account.")
        return redirect('home')

    # Allow member to upload payment proof if not already uploaded
    if request.method == 'POST' and 'update_payment' in request.POST:
        tx_id = request.POST.get('transaction_id', '').strip()
        screenshot = request.FILES.get('payment_screenshot')
        if tx_id:
            app.transaction_id = tx_id
        if screenshot:
            app.payment_screenshot = screenshot
        app.save()
        messages.success(request, "Payment details submitted for verification!")
        return redirect('member_dashboard')

    return render(request, 'membership/member_dashboard.html', {'app': app})


def get_filtered_queryset(request):
    queryset = MembershipApplication.objects.all()

    # Search filter
    q = request.GET.get('q', '').strip()
    if q:
        queryset = queryset.filter(
            Q(full_name__icontains=q) |
            Q(application_no__icontains=q) |
            Q(institution__icontains=q) |
            Q(mobile__icontains=q) |
            Q(email__icontains=q) |
            Q(wing__icontains=q) |
            Q(other_wing__icontains=q) |
            Q(transaction_id__icontains=q)
        )

    # Wing filter
    wing_filter = request.GET.get('wing', '').strip()
    if wing_filter:
        queryset = queryset.filter(wing=wing_filter)

    # District filter
    district_filter = request.GET.get('district', '').strip()
    if district_filter:
        queryset = queryset.filter(district=district_filter)

    # Tab filter
    tab = request.GET.get('tab', 'all').strip().lower()
    if tab == 'unverified':
        queryset = queryset.filter(status='Pending')
    elif tab == 'verified':
        queryset = queryset.filter(status='Approved')
    elif tab == 'rejected':
        queryset = queryset.filter(status='Rejected')

    # Status filter (explicit override)
    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        queryset = queryset.filter(status=status_filter)

    # Payment Status filter
    payment_filter = request.GET.get('payment_status', '').strip()
    if payment_filter:
        queryset = queryset.filter(payment_status=payment_filter)

    # Sorting
    sort_by = request.GET.get('sort', 'newest').strip()
    valid_sorts = {
        'newest': ['-created_at'],
        '-created_at': ['-created_at'],
        'oldest': ['created_at'],
        'created_at': ['created_at'],
        'wing_asc': ['wing', 'other_wing', 'full_name'],
        'wing_desc': ['-wing', '-other_wing', 'full_name'],
        'name_asc': ['full_name'],
        'name_desc': ['-full_name'],
        'institution_asc': ['institution', 'full_name'],
        'district_asc': ['district', 'full_name'],
    }
    order_fields = valid_sorts.get(sort_by, ['-created_at'])
    if isinstance(order_fields, (list, tuple)):
        return queryset.order_by(*order_fields)
    return queryset.order_by(order_fields)


@login_required(login_url='/login/')
def admin_portal_view(request):
    """Administrative dashboard to manage, verify, accept/reject, filter, search, sort, and export."""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Access restricted to administrators.")
        return redirect('member_dashboard')

    queryset = get_filtered_queryset(request)
    q = request.GET.get('q', '').strip()
    wing_filter = request.GET.get('wing', '').strip()
    district_filter = request.GET.get('district', '').strip()
    status_filter = request.GET.get('status', '').strip()
    payment_filter = request.GET.get('payment_status', '').strip()
    sort_by = request.GET.get('sort', 'newest').strip()
    tab = request.GET.get('tab', 'all').strip().lower()

    # KPI counts across all applications
    total_count = MembershipApplication.objects.count()
    approved_count = MembershipApplication.objects.filter(status='Approved').count()
    pending_count = MembershipApplication.objects.filter(status='Pending').count()
    rejected_count = MembershipApplication.objects.filter(status='Rejected').count()
    payment_verified_count = MembershipApplication.objects.filter(payment_status='Verified').count()
    payment_pending_count = MembershipApplication.objects.filter(payment_status='Pending Verification').count()

    districts = [d[0] for d in MembershipApplication.DISTRICT_CHOICES]
    wings = [w[0] for w in MembershipApplication.WING_CHOICES]

    context = {
        'applications': queryset,
        'total_count': total_count,
        'approved_count': approved_count,
        'pending_count': pending_count,
        'rejected_count': rejected_count,
        'payment_verified_count': payment_verified_count,
        'payment_pending_count': payment_pending_count,
        'filtered_count': queryset.count(),
        'districts': districts,
        'wings': wings,
        'current_q': q,
        'current_wing': wing_filter,
        'current_district': district_filter,
        'current_status': status_filter,
        'current_payment': payment_filter,
        'current_sort': sort_by,
        'current_tab': tab,
    }
    return render(request, 'membership/admin_portal.html', context)


@login_required(login_url='/login/')
def admin_quick_action_view(request, pk, action):
    """Unified 1-Click Verification actions: accept (both payment & profile), reject (with reason), and delete."""
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('member_dashboard')

    app = get_object_or_404(MembershipApplication, pk=pk)

    if action == 'delete':
        user_to_delete = app.user
        app_name = app.full_name
        app.delete()
        if user_to_delete and not user_to_delete.is_superuser:
            user_to_delete.delete()
        messages.success(request, f"Application and account for {app_name} have been permanently deleted.")
        return redirect('admin_portal')

    if action == 'accept':
        app.status = 'Approved'
        app.payment_status = 'Verified'
        app.verified_at = timezone.now()
        app.rejection_reason = ''
        if not app.membership_no:
            app.membership_no = f"KSFCTA/MEM/{app.created_at.year}/{app.id:04d}"
        if not app.approved_by:
            app.approved_by = "Shafi K (State Treasurer)"
        app.save()
        messages.success(request, f"✔ Application & Payment for {app.full_name} ({app.application_no}) ACCEPTED and officially VERIFIED!")

    elif action == 'reject':
        reason = request.POST.get('rejection_reason', '').strip() or request.GET.get('reason', '').strip() or "Payment receipt or submitted details could not be verified."
        app.status = 'Rejected'
        app.payment_status = 'Rejected'
        app.rejection_reason = reason
        app.save()
        messages.warning(request, f"Application for {app.full_name} marked as REJECTED. Reason recorded: {reason}")

    elif action == 'verify_payment':
        app.payment_status = 'Verified'
        app.save()
        messages.success(request, f"Payment for {app.full_name} marked as Verified!")

    return redirect(request.META.get('HTTP_REFERER', 'admin_portal'))


@login_required(login_url='/login/')
def admin_member_detail_view(request, pk):
    """View full single application details with verification controls and rejection reason."""
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('member_dashboard')

    app = get_object_or_404(MembershipApplication, pk=pk)

    if request.method == 'POST':
        app.status = request.POST.get('status', app.status)
        app.payment_status = request.POST.get('payment_status', app.payment_status)
        app.membership_no = request.POST.get('membership_no', app.membership_no).strip()
        app.receipt_no = request.POST.get('receipt_no', app.receipt_no).strip()
        app.membership_fee = request.POST.get('membership_fee', app.membership_fee).strip()
        app.approved_by = request.POST.get('approved_by', app.approved_by).strip()
        app.admin_notes = request.POST.get('admin_notes', app.admin_notes).strip()
        app.rejection_reason = request.POST.get('rejection_reason', app.rejection_reason).strip()
        
        # If admin marks as Approved, ensure payment is verified and verified_at timestamp is set
        if app.status == 'Approved':
            app.payment_status = 'Verified'
            if not app.verified_at:
                app.verified_at = timezone.now()
            if not app.membership_no:
                app.membership_no = f"KSFCTA/MEM/{app.created_at.year}/{app.id:04d}"
            app.rejection_reason = ''
        elif app.status == 'Rejected':
            app.payment_status = 'Rejected'

        app.save()
        messages.success(request, f"Updated verification details for {app.full_name} ({app.application_no}).")
        return redirect('admin_member_detail', pk=app.id)

    return render(request, 'membership/member_detail.html', {'app': app})


@login_required(login_url='/login/')
def admin_wings_view(request):
    """Dedicated view for each Wing with counts, sorting, and 1-click dedicated downloads."""
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('member_dashboard')

    wings_list = [w[0] for w in MembershipApplication.WING_CHOICES]
    selected_wing = request.GET.get('wing', wings_list[0]).strip()
    if selected_wing not in wings_list and selected_wing != 'Other':
        selected_wing = wings_list[0]

    # Queryset for this wing
    queryset = MembershipApplication.objects.filter(wing=selected_wing)

    q = request.GET.get('q', '').strip()
    if q:
        queryset = queryset.filter(
            Q(full_name__icontains=q) |
            Q(application_no__icontains=q) |
            Q(institution__icontains=q) |
            Q(mobile__icontains=q) |
            Q(email__icontains=q) |
            Q(other_wing__icontains=q) |
            Q(transaction_id__icontains=q)
        )

    # Sort
    sort_by = request.GET.get('sort', 'newest').strip()
    valid_sorts = {
        'newest': ['-created_at'],
        'oldest': ['created_at'],
        'name_asc': ['full_name'],
        'name_desc': ['-full_name'],
        'district_asc': ['district', 'full_name'],
        'institution_asc': ['institution', 'full_name'],
    }
    order_fields = valid_sorts.get(sort_by, ['-created_at'])
    queryset = queryset.order_by(*order_fields)

    # Counts for this wing
    wing_total = MembershipApplication.objects.filter(wing=selected_wing).count()
    wing_approved = MembershipApplication.objects.filter(wing=selected_wing, status='Approved').count()
    wing_pending = MembershipApplication.objects.filter(wing=selected_wing, status='Pending').count()
    wing_rejected = MembershipApplication.objects.filter(wing=selected_wing, status='Rejected').count()

    # Wing count map for badges
    wing_counts = {
        w: MembershipApplication.objects.filter(wing=w).count() for w in wings_list
    }

    context = {
        'wings_list': wings_list,
        'selected_wing': selected_wing,
        'applications': queryset,
        'wing_total': wing_total,
        'wing_approved': wing_approved,
        'wing_pending': wing_pending,
        'wing_rejected': wing_rejected,
        'wing_counts': wing_counts,
        'current_q': q,
        'current_sort': sort_by,
        'filtered_count': queryset.count(),
    }
    return render(request, 'membership/admin_wings.html', context)


@login_required(login_url='/login/')
def admin_districts_view(request):
    """Dedicated view for each District with counts, sorting, and 1-click dedicated downloads."""
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('member_dashboard')

    districts_list = [d[0] for d in MembershipApplication.DISTRICT_CHOICES]
    selected_district = request.GET.get('district', districts_list[0]).strip()
    if selected_district not in districts_list:
        selected_district = districts_list[0]

    # Queryset for this district
    queryset = MembershipApplication.objects.filter(district=selected_district)

    q = request.GET.get('q', '').strip()
    if q:
        queryset = queryset.filter(
            Q(full_name__icontains=q) |
            Q(application_no__icontains=q) |
            Q(institution__icontains=q) |
            Q(mobile__icontains=q) |
            Q(email__icontains=q) |
            Q(wing__icontains=q) |
            Q(other_wing__icontains=q) |
            Q(transaction_id__icontains=q)
        )

    # Sort
    sort_by = request.GET.get('sort', 'newest').strip()
    valid_sorts = {
        'newest': ['-created_at'],
        'oldest': ['created_at'],
        'name_asc': ['full_name'],
        'name_desc': ['-full_name'],
        'wing_asc': ['wing', 'other_wing', 'full_name'],
        'institution_asc': ['institution', 'full_name'],
    }
    order_fields = valid_sorts.get(sort_by, ['-created_at'])
    queryset = queryset.order_by(*order_fields)

    # Counts for this district
    district_total = MembershipApplication.objects.filter(district=selected_district).count()
    district_approved = MembershipApplication.objects.filter(district=selected_district, status='Approved').count()
    district_pending = MembershipApplication.objects.filter(district=selected_district, status='Pending').count()
    district_rejected = MembershipApplication.objects.filter(district=selected_district, status='Rejected').count()

    # District count map for badges
    district_counts = {
        d: MembershipApplication.objects.filter(district=d).count() for d in districts_list
    }

    context = {
        'districts_list': districts_list,
        'selected_district': selected_district,
        'applications': queryset,
        'district_total': district_total,
        'district_approved': district_approved,
        'district_pending': district_pending,
        'district_rejected': district_rejected,
        'district_counts': district_counts,
        'current_q': q,
        'current_sort': sort_by,
        'filtered_count': queryset.count(),
    }
    return render(request, 'membership/admin_districts.html', context)


@login_required(login_url='/login/')
def export_excel_view(request):
    """Export current filtered & sorted set to Excel (.xlsx)."""
    queryset = get_filtered_queryset(request)
    return export_applications_to_excel(queryset)


@login_required(login_url='/login/')
def export_single_docx_view(request, pk):
    """Download official Microsoft Word (.docx) application. Only for admin or approved members."""
    app = get_object_or_404(MembershipApplication, pk=pk)
    is_admin = request.user.is_staff or request.user.is_superuser
    is_own_member = hasattr(request.user, 'application') and request.user.application.id == app.id

    if is_admin:
        return export_single_application_docx(app)

    if not is_own_member:
        messages.error(request, "Unauthorized access.")
        return redirect('home')

    if app.status != 'Approved':
        messages.warning(request, "Your documents will be available for download only after admin verification and approval.")
        return redirect('member_dashboard')

    return export_single_application_docx(app)


def export_letterhead_pdf_view(request, pk):
    """
    Download official Membership Certificate merged on the official letterhead.
    Allowed for admin always. For members: ONLY if status is Approved.
    """
    app = get_object_or_404(MembershipApplication, pk=pk)
    is_admin = request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)
    is_own_member = request.user.is_authenticated and hasattr(request.user, 'application') and request.user.application.id == app.id

    if is_admin:
        # Admin can always download
        return export_letterhead_certificate_pdf(app)

    if not is_own_member:
        messages.error(request, "Unauthorized access.")
        return redirect('home')

    # Members can only download if approved
    if app.status != 'Approved':
        messages.warning(request, "Your certificate will be available for download only after admin verification and approval.")
        return redirect('member_dashboard')

    return export_letterhead_certificate_pdf(app)


@login_required(login_url='/login/')
def export_summary_pdf_view(request):
    """Download master PDF summary list sorted and filtered."""
    queryset = get_filtered_queryset(request)
    return export_summary_pdf(queryset)
