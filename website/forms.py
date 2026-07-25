from django import forms
from .models import CustomerFeedback
from .image_utils import validate_image_file, optimize_image

class CustomerFeedbackForm(forms.ModelForm):
    avatar_file = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={'class': 'floating-input', 'accept': 'image/*', 'id': 'fbCustAvatar', 'style': 'height: 58px !important; padding-top: 22px !important; cursor: pointer;'}),
        label="Your Photo / Avatar *"
    )

    class Meta:
        model = CustomerFeedback
        fields = ['customer_name', 'email', 'rating', 'comment', 'avatar_file']
        widgets = {
            'customer_name': forms.TextInput(attrs={
                'class': 'floating-input',
                'placeholder': ' ',
                'id': 'fbCustName',
                'required': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'floating-input',
                'placeholder': ' ',
                'id': 'fbCustEmail',
            }),
            'rating': forms.Select(
                choices=[(i, f"{i} ★ - {'Excellent' if i==5 else 'Very Good' if i==4 else 'Good' if i==3 else 'Fair' if i==2 else 'Poor'}") for i in range(5, 0, -1)],
                attrs={
                    'class': 'floating-input',
                    'id': 'fbCustRating',
                    'style': 'background: var(--color-bg-deep); color: var(--color-primary); font-weight: 600;'
                }
            ),
            'comment': forms.Textarea(attrs={
                'class': 'floating-input',
                'placeholder': ' ',
                'id': 'fbCustComment',
                'rows': 4,
                'required': True,
            }),
        }

    def clean_avatar_file(self):
        avatar_file = self.cleaned_data.get('avatar_file')
        if avatar_file:
            validate_image_file(avatar_file)
            avatar_file = optimize_image(avatar_file, prefix='rev')
        return avatar_file
