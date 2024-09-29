from django import forms
from account.models import User  
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['first_name', 'last_name', 'email','username',  'password1', 'password2' ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None
        self.fields['username'].help_text = None
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control m-2'


class UserLoginForm(forms.Form):  
    username = forms.CharField(label="Username",max_length=50)  
    password = forms.CharField(label="Password", max_length = 100)  
    
    def __init__(self, *args, **kwargs):
        super(UserLoginForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control m-2'

def validate_username(username):        
    if User.objects.filter(username=username).exists():
        raise ValidationError("Username already exists.")
    
def validate_email(user_email):        
    if User.objects.filter(email=user_email).exists():
        raise ValidationError("Email  already exists.")


class UserprofileUpdate(forms.ModelForm):
    # specify the name of model to use
    class Meta:
        model = User
        fields = ["first_name", "last_name", "username" ,  "email" ]

    def __init__(self, *args, **kwargs):
        super(UserprofileUpdate, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control m-1'