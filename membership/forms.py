from django import forms
from django.contrib.auth.models import User
from .models import MembershipApplication

class MembershipRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Create a password for your account',
            'required': True,
            'id': 'id_password'
        }),
        label="Create Account Password",
        min_length=6,
        help_text="Minimum 6 characters. You will use your Email and this Password to log in."
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Confirm your password',
            'required': True,
            'id': 'id_confirm_password'
        }),
        label="Confirm Account Password"
    )

    transaction_id = forms.CharField(
        required=True,
        error_messages={'required': 'Transaction ID / UTR Number is required to verify your payment.'},
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter 12-digit UPI / UTR / Transaction ID (Mandatory)',
            'required': True,
            'id': 'id_transaction_id'
        }),
        label="Transaction ID / UTR Number"
    )

    photo = forms.ImageField(
        required=True,
        error_messages={'required': 'Passport-size photo is mandatory for your membership card / certificate.'},
        widget=forms.FileInput(attrs={
            'class': 'form-file',
            'accept': 'image/*',
            'required': True,
            'id': 'id_photo'
        }),
        label="Passport Size Photograph (Mandatory for Membership Card)"
    )

    payment_screenshot = forms.ImageField(
        required=True,
        error_messages={'required': 'Payment receipt screenshot is required to verify your payment.'},
        widget=forms.FileInput(attrs={
            'class': 'form-file',
            'accept': 'image/*',
            'required': True,
            'id': 'id_payment_screenshot'
        }),
        label="Upload Payment Receipt Screenshot"
    )

    declaration = forms.BooleanField(
        required=True,
        error_messages={'required': 'You must agree to the declaration to complete registration.'},
        label="I hereby declare that the information furnished above is true and correct to the best of my knowledge. I agree to abide by the Constitution, Rules and Regulations of the Self Financing College Teachers Association & Staff Union."
    )

    class Meta:
        model = MembershipApplication
        fields = [
            'full_name',
            'gender',
            'dob',
            'mobile',
            'email',
            'wing',
            'other_wing',
            'institution',
            'designation',
            'department',
            'category',
            'address',
            'pincode',
            'district',
            'membership_type',
            'photo',
            'transaction_id',
            'payment_screenshot',
            'declaration',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter your full name (in block letters)',
                'style': 'text-transform: uppercase;',
                'required': True,
                'id': 'id_full_name'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
                'id': 'id_gender'
            }),
            'dob': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date',
                'required': True,
                'id': 'id_dob'
            }),
            'mobile': forms.TextInput(attrs={
                'class': 'form-input',
                'type': 'tel',
                'placeholder': '10-digit mobile number',
                'pattern': '[0-9]{10}',
                'required': True,
                'id': 'id_mobile'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'name@example.com (Your Login Username)',
                'required': True,
                'id': 'id_email'
            }),
            'wing': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
                'id': 'id_wing',
                'onchange': 'handleWingChange(this)'
            }),
            'other_wing': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Please specify your Wing name',
                'id': 'id_other_wing'
            }),
            'institution': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Name of Self Financing College / Institution',
                'required': True,
                'id': 'id_institution'
            }),
            'designation': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g. Assistant Professor, Lecturer, HOD, Principal',
                'required': True,
                'id': 'id_designation'
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g. Computer Science, Commerce, English, Management',
                'required': True,
                'id': 'id_department'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
                'id': 'id_category'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Your permanent residential address',
                'rows': 3,
                'required': True,
                'id': 'id_address'
            }),
            'pincode': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '6-digit PIN code',
                'pattern': '[0-9]{6}',
                'required': True,
                'id': 'id_pincode'
            }),
            'district': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
                'id': 'id_district'
            }),
            'membership_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
                'id': 'id_membership_type'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-file',
                'accept': 'image/*',
                'id': 'id_photo'
            }),
            'payment_screenshot': forms.FileInput(attrs={
                'class': 'form-file',
                'accept': 'image/*',
                'id': 'id_payment_screenshot'
            }),
            'declaration': forms.CheckboxInput(attrs={
                'class': 'form-checkbox',
                'id': 'id_declaration'
            })
        }

    def clean_full_name(self):
        name = self.cleaned_data.get('full_name', '')
        return name.strip().upper()

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(username=email).exists() or MembershipApplication.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email address already exists. Please login instead.")
        return email

    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile', '')
        mobile = ''.join(c for c in mobile if c.isdigit())
        if len(mobile) != 10:
            raise forms.ValidationError("Please enter a valid 10-digit mobile number.")
        return mobile

    def clean_pincode(self):
        pin = self.cleaned_data.get('pincode', '')
        pin = ''.join(c for c in pin if c.isdigit())
        if len(pin) != 6:
            raise forms.ValidationError("Please enter a valid 6-digit PIN code.")
        return pin

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('confirm_password')
        if p1 and p2 and p1 != p2:
            self.add_error('confirm_password', "Passwords do not match. Please re-enter carefully.")
        
        wing = cleaned_data.get('wing')
        other_wing = cleaned_data.get('other_wing', '').strip()
        if wing == 'Other' and not other_wing:
            self.add_error('other_wing', "Please specify your Wing name.")
        return cleaned_data
        
    def save(self, commit=True):
        import base64
        instance = super().save(commit=False)
        
        # Convert uploaded photo to base64
        photo_file = self.cleaned_data.get('photo')
        if photo_file and hasattr(photo_file, 'read'):
            encoded = base64.b64encode(photo_file.read()).decode('utf-8')
            instance.photo = f"data:{photo_file.content_type};base64,{encoded}"
            
        # Convert uploaded screenshot to base64
        payment_file = self.cleaned_data.get('payment_screenshot')
        if payment_file and hasattr(payment_file, 'read'):
            encoded = base64.b64encode(payment_file.read()).decode('utf-8')
            instance.payment_screenshot = f"data:{payment_file.content_type};base64,{encoded}"
            
        if commit:
            instance.save()
        return instance
