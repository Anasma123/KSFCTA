from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class MembershipApplication(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    CATEGORY_CHOICES = [
        ('Principal', 'Principal'),
        ('Teaching', 'Teaching'),
        ('Non teaching', 'Non teaching'),
    ]

    WING_CHOICES = [
        ('Arts and sciences', 'Arts and sciences'),
        ('Teacher Education', 'Teacher Education'),
        ('Law colleges', 'Law colleges'),
        ('Engineering Colleges', 'Engineering Colleges'),
        ('Health and Allied Sciences', 'Health and Allied Sciences'),
        ('Principal', 'Principal'),
        ('Administrative Staffs', 'Administrative Staffs'),
        ('Other', 'Other (Please Specify)'),
    ]

    MEMBERSHIP_TYPE_CHOICES = [
        ('Annual Membership', 'Annual Membership'),
        ('Life Membership', 'Life Membership'),
    ]

    DISTRICT_CHOICES = [
        ('Thiruvananthapuram', 'Thiruvananthapuram'),
        ('Kollam', 'Kollam'),
        ('Pathanamthitta', 'Pathanamthitta'),
        ('Alappuzha', 'Alappuzha'),
        ('Kottayam', 'Kottayam'),
        ('Idukki', 'Idukki'),
        ('Ernakulam', 'Ernakulam'),
        ('Thrissur', 'Thrissur'),
        ('Palakkad', 'Palakkad'),
        ('Malappuram', 'Malappuram'),
        ('Kozhikode', 'Kozhikode'),
        ('Wayanad', 'Wayanad'),
        ('Kannur', 'Kannur'),
        ('Kasaragod', 'Kasaragod'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending Review'),
        ('Approved', 'Approved / Accepted'),
        ('Rejected', 'Rejected'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('Pending Verification', 'Pending Verification'),
        ('Verified', 'Verified'),
        ('Rejected', 'Payment Rejected'),
    ]

    # Linked User account for member login (using Email as username)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='application')

    # Application ID
    application_no = models.CharField(max_length=30, unique=True, editable=False)

    # 1. Name in Block Letters
    full_name = models.CharField(max_length=200, verbose_name="Name (in Block Letters)")

    # 2. Gender
    gender = models.CharField(max_length=15, choices=GENDER_CHOICES, verbose_name="Gender")

    # 3. Date of Birth
    dob = models.DateField(verbose_name="Date of Birth")

    # 4. Mobile Number
    mobile = models.CharField(max_length=15, verbose_name="Mobile Number")

    # 5. Email ID (Used as Login Username)
    email = models.EmailField(verbose_name="Email ID", unique=True)

    # Wings
    wing = models.CharField(max_length=50, choices=WING_CHOICES, default='Arts and sciences', verbose_name="Wing")
    other_wing = models.CharField(max_length=150, blank=True, default='', verbose_name="Other Wing (Specify)")

    # 6. Name of Institution
    institution = models.CharField(max_length=250, verbose_name="Name of Institution")

    # 7. Designation
    designation = models.CharField(max_length=150, verbose_name="Designation")

    # 8. Department
    department = models.CharField(max_length=150, verbose_name="Department")

    # 9. Category
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='Teaching', verbose_name="Category")

    # 10. Address & Pin
    address = models.TextField(verbose_name="Permanent Address")
    pincode = models.CharField(max_length=10, verbose_name="Pin Code")
    district = models.CharField(max_length=50, choices=DISTRICT_CHOICES, default='Thiruvananthapuram', verbose_name="District")

    # 11. Type of Membership
    membership_type = models.CharField(max_length=30, choices=MEMBERSHIP_TYPE_CHOICES, default='Annual Membership', verbose_name="Type of Membership")

    # Payment Details (Fee: ₹ 200)
    membership_fee = models.CharField(max_length=100, default='₹ 200', verbose_name="Membership Fee")
    # 12. Passport Size Photo (Stored as Base64 string)
    photo = models.TextField(null=True, blank=True, verbose_name="Base64 Photo")

    # Payment details
    transaction_id = models.CharField(max_length=150, blank=True, null=True, verbose_name="Transaction ID / UTR No")
    
    # Stored as Base64 string
    payment_screenshot = models.TextField(null=True, blank=True, verbose_name="Base64 Payment Screenshot")
    payment_status = models.CharField(max_length=30, choices=PAYMENT_STATUS_CHOICES, default='Pending Verification', verbose_name="Payment Status")

    # Declaration
    declaration = models.BooleanField(default=True, verbose_name="Agreed to Declaration")

    # Office Verification & Approval Fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending', verbose_name="Application Status")
    receipt_no = models.CharField(max_length=100, blank=True, default='', verbose_name="Receipt No")
    membership_no = models.CharField(max_length=100, blank=True, default='', verbose_name="Membership No")
    approved_by = models.CharField(max_length=150, blank=True, default='', verbose_name="Approved By")
    admin_notes = models.TextField(blank=True, default='', verbose_name="Office Notes")
    rejection_reason = models.TextField(blank=True, default='', verbose_name="Rejection Reason")
    verified_at = models.DateTimeField(null=True, blank=True, verbose_name="Verified Date")

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Application Date")
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def display_wing(self):
        if self.wing == 'Other' and self.other_wing:
            return f"Other ({self.other_wing})"
        return self.wing

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Membership Application"
        verbose_name_plural = "Membership Applications"

    def __str__(self):
        return f"{self.application_no} - {self.full_name} ({self.wing})"

    def save(self, *args, **kwargs):
        if not self.application_no:
            count = MembershipApplication.objects.count() + 1
            year = timezone.now().year
            self.application_no = f"KSFCTA-{year}-{count:04d}"
        super().save(*args, **kwargs)
