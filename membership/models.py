from django.db import models
from django.utils import timezone

class MembershipApplication(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    CATEGORY_CHOICES = [
        ('Teaching Staff', 'Teaching Staff'),
        ('Non-Teaching Staff', 'Non-Teaching Staff'),
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
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

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

    # 5. Email ID
    email = models.EmailField(verbose_name="Email ID")

    # 6. Name of Institution
    institution = models.CharField(max_length=250, verbose_name="Name of Institution")

    # 7. Designation
    designation = models.CharField(max_length=150, verbose_name="Designation")

    # 8. Department
    department = models.CharField(max_length=150, verbose_name="Department")

    # 9. Category
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='Teaching Staff', verbose_name="Category")

    # 10. Address & Pin
    address = models.TextField(verbose_name="Permanent Address")
    pincode = models.CharField(max_length=10, verbose_name="Pin Code")
    district = models.CharField(max_length=50, choices=DISTRICT_CHOICES, default='Thiruvananthapuram', verbose_name="District")

    # 11. Type of Membership
    membership_type = models.CharField(max_length=30, choices=MEMBERSHIP_TYPE_CHOICES, default='Annual Membership', verbose_name="Type of Membership")

    # Photo (Optional)
    photo = models.ImageField(upload_to='photos/%Y/%m/', blank=True, null=True, verbose_name="Applicant Photo")

    # Declaration
    declaration = models.BooleanField(default=True, verbose_name="Agreed to Declaration")

    # Office Use Only Fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    membership_fee = models.CharField(max_length=100, blank=True, default='', verbose_name="Membership Fee Received")
    receipt_no = models.CharField(max_length=100, blank=True, default='', verbose_name="Receipt No")
    membership_no = models.CharField(max_length=100, blank=True, default='', verbose_name="Membership No")
    approved_by = models.CharField(max_length=150, blank=True, default='', verbose_name="Approved By")
    admin_notes = models.TextField(blank=True, default='', verbose_name="Office Notes")

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Application Date")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Membership Application"
        verbose_name_plural = "Membership Applications"

    def __str__(self):
        return f"{self.application_no} - {self.full_name} ({self.institution})"

    def save(self, *args, **kwargs):
        if not self.application_no:
            count = MembershipApplication.objects.count() + 1
            year = timezone.now().year
            self.application_no = f"KSFCTA-{year}-{count:04d}"
        super().save(*args, **kwargs)
