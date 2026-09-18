from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse
from .models import MembershipApplication
from .forms import MembershipRegistrationForm
from .exports import (
    export_applications_to_excel,
    export_single_application_docx,
    export_single_application_pdf,
    export_summary_pdf
)


def home_view(request):
    """Public home page for KSFCTA Membership Campaign 2026."""
    success_app = None
    form = MembershipRegistrationForm()

    if request.method == 'POST':
        form = MembershipRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            app = form.save()
            request.session['registered_app_id'] = app.id
            messages.success(request, f"Registration Successful! Your Application No is {app.application_no}")
            return redirect('registration_success', pk=app.id)

    registered_count = MembershipApplication.objects.count()
    context = {
        'form': form,
        'registered_count': registered_count,
    }
    return render(request, 'membership/index.html', context)


def registration_success_view(request, pk):
    """Confirmation page with member slip and instant download options."""
    app = get_object_or_404(MembershipApplication, pk=pk)
    return render(request, 'membership/success.html', {'app': app})


def login_view(request):
    """Secure, discreet administrative login page accessible via /login."""
    if request.user.is_authenticated:
        return redirect('admin_portal')

    error_msg = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_active:
            login(request, user)
            return redirect('admin_portal')
        else:
            error_msg = "Invalid username or password. Please verify credentials."

    return render(request, 'membership/login.html', {'error_msg': error_msg})


def logout_view(request):
    """Log out admin user."""
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')


@login_required(login_url='/login/')
def admin_portal_view(request):
    """Administrative dashboard to manage, filter, search, sort, and export registrations."""
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
            Q(department__icontains=q)
        )

    # District filter
    district_filter = request.GET.get('district', '').strip()
    if district_filter:
        queryset = queryset.filter(district=district_filter)

    # Membership type filter
    type_filter = request.GET.get('type', '').strip()
    if type_filter:
        queryset = queryset.filter(membership_type=type_filter)

    # Category filter
    category_filter = request.GET.get('category', '').strip()
    if category_filter:
        queryset = queryset.filter(category=category_filter)

    # Status filter
    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        queryset = queryset.filter(status=status_filter)

    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    valid_sorts = {
        'newest': '-created_at',
        'oldest': 'created_at',
        'name_asc': 'full_name',
        'name_desc': '-full_name',
        'institution_asc': 'institution',
        'district_asc': 'district',
        'app_asc': 'application_no',
    }
    order_field = valid_sorts.get(sort_by, '-created_at')
    queryset = queryset.order_by(order_field)

    # Counts & Metrics
    total_count = MembershipApplication.objects.count()
    teaching_count = MembershipApplication.objects.filter(category='Teaching Staff').count()
    non_teaching_count = MembershipApplication.objects.filter(category='Non-Teaching Staff').count()
    annual_count = MembershipApplication.objects.filter(membership_type='Annual Membership').count()
    life_count = MembershipApplication.objects.filter(membership_type='Life Membership').count()
    approved_count = MembershipApplication.objects.filter(status='Approved').count()
    pending_count = MembershipApplication.objects.filter(status='Pending').count()

    # District choices for filter dropdown
    districts = [d[0] for d in MembershipApplication.DISTRICT_CHOICES]

    context = {
        'applications': queryset,
        'total_count': total_count,
        'teaching_count': teaching_count,
        'non_teaching_count': non_teaching_count,
        'annual_count': annual_count,
        'life_count': life_count,
        'approved_count': approved_count,
        'pending_count': pending_count,
        'filtered_count': queryset.count(),
        'districts': districts,
        'current_q': q,
        'current_district': district_filter,
        'current_type': type_filter,
        'current_category': category_filter,
        'current_status': status_filter,
        'current_sort': sort_by,
    }
    return render(request, 'membership/admin_portal.html', context)


@login_required(login_url='/login/')
def admin_member_detail_view(request, pk):
    """View full single application details with status update controls."""
    app = get_object_or_404(MembershipApplication, pk=pk)

    if request.method == 'POST':
        app.status = request.POST.get('status', app.status)
        app.membership_no = request.POST.get('membership_no', app.membership_no).strip()
        app.receipt_no = request.POST.get('receipt_no', app.receipt_no).strip()
        app.membership_fee = request.POST.get('membership_fee', app.membership_fee).strip()
        app.approved_by = request.POST.get('approved_by', app.approved_by).strip()
        app.admin_notes = request.POST.get('admin_notes', app.admin_notes).strip()
        app.save()
        messages.success(request, f"Updated application details for {app.full_name} ({app.application_no}).")
        return redirect('admin_member_detail', pk=app.id)

    return render(request, 'membership/member_detail.html', {'app': app})


@login_required(login_url='/login/')
def export_excel_view(request):
    """Export current filtered set or all members to Excel (.xlsx)."""
    queryset = MembershipApplication.objects.all().order_by('-created_at')
    # Apply same filters if provided
    q = request.GET.get('q', '').strip()
    if q:
        queryset = queryset.filter(Q(full_name__icontains=q) | Q(institution__icontains=q) | Q(mobile__icontains=q))
    district = request.GET.get('district', '').strip()
    if district:
        queryset = queryset.filter(district=district)
    return export_applications_to_excel(queryset)


@login_required(login_url='/login/')
def export_single_docx_view(request, pk):
    """Download official Microsoft Word (.docx) application matching membership form.docx."""
    app = get_object_or_404(MembershipApplication, pk=pk)
    return export_single_application_docx(app)


@login_required(login_url='/login/')
def export_single_pdf_view(request, pk):
    """Download printable official PDF membership form."""
    app = get_object_or_404(MembershipApplication, pk=pk)
    return export_single_application_pdf(app)


@login_required(login_url='/login/')
def export_summary_pdf_view(request):
    """Download master PDF summary list of all registered teachers."""
    queryset = MembershipApplication.objects.all().order_by('-created_at')
    return export_summary_pdf(queryset)
