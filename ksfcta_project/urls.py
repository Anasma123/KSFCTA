from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from membership import views

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', views.home_view, name='home'),
    path('registration-success/<int:pk>/', views.registration_success_view, name='registration_success'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('admin-portal/', views.admin_portal_view, name='admin_portal'),
    path('admin-portal/member/<int:pk>/', views.admin_member_detail_view, name='admin_member_detail'),
    path('export/excel/', views.export_excel_view, name='export_excel'),
    path('export/docx/<int:pk>/', views.export_single_docx_view, name='export_single_docx'),
    path('export/pdf/<int:pk>/', views.export_single_pdf_view, name='export_single_pdf'),
    path('export/pdf-summary/', views.export_summary_pdf_view, name='export_summary_pdf'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
