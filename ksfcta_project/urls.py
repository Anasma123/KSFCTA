from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from membership import views

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', views.home_view, name='home'),
    path('registration-success/<int:pk>/', views.registration_success_view, name='registration_success'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('member-dashboard/', views.member_dashboard_view, name='member_dashboard'),
    path('admin-portal/', views.admin_portal_view, name='admin_portal'),
    path('admin-portal/wings/', views.admin_wings_view, name='admin_wings'),
    path('admin-portal/districts/', views.admin_districts_view, name='admin_districts'),
    path('admin-portal/member/<int:pk>/', views.admin_member_detail_view, name='admin_member_detail'),
    path('admin-portal/action/<int:pk>/<str:action>/', views.admin_quick_action_view, name='admin_quick_action'),
    path('export/excel/', views.export_excel_view, name='export_excel'),
    path('export/docx/<int:pk>/', views.export_single_docx_view, name='export_single_docx'),
    path('export/letterhead-pdf/<int:pk>/', views.export_letterhead_pdf_view, name='export_letterhead_pdf'),
    path('export/pdf-summary/', views.export_summary_pdf_view, name='export_summary_pdf'),
]

import os
from django.urls import re_path
from django.views.static import serve
from django.http import Http404

def serve_static_fallback(request, path):
    # Check STATIC_ROOT first
    target = os.path.join(settings.STATIC_ROOT, path)
    if os.path.exists(target) and os.path.isfile(target):
        response = serve(request, path, document_root=settings.STATIC_ROOT)
        response['Cache-Control'] = 'public, max-age=86400'
        return response
    # Check each directory in STATICFILES_DIRS
    for sdir in getattr(settings, 'STATICFILES_DIRS', []):
        target = os.path.join(str(sdir), path)
        if os.path.exists(target) and os.path.isfile(target):
            response = serve(request, path, document_root=str(sdir))
            response['Cache-Control'] = 'public, max-age=86400'
            return response
    raise Http404(f"Static file '{path}' not found")

def serve_media_fallback(request, path):
    return serve(request, path, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    re_path(r'^static/(?P<path>.*)$', serve_static_fallback, name='static_fallback'),
    re_path(r'^media/(?P<path>.*)$', serve_media_fallback, name='media_fallback'),
]
