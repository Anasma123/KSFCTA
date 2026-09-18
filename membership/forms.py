from django import forms
from .models import MembershipApplication

class MembershipRegistrationForm(forms.ModelForm):
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
            'institution',
            'designation',
            'department',
            'category',
            'address',
            'pincode',
            'district',
            'membership_type',
            'photo',
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
                'placeholder': 'name@example.com',
                'required': True,
                'id': 'id_email'
            }),
            'institution': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Name of Self Financing College / Institution',
                'required': True,
                'id': 'id_institution'
            }),
            'designation': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g. Assistant Professor, Lecturer, HOD',
                'required': True,
                'id': 'id_designation'
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g. Computer Science, Commerce, English',
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
            'declaration': forms.CheckboxInput(attrs={
                'class': 'form-checkbox',
                'id': 'id_declaration'
            })
        }

    def clean_full_name(self):
        name = self.cleaned_data.get('full_name', '')
        return name.strip().upper()

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
