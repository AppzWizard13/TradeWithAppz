from django import forms
from django.conf import settings
from .models import TradingConfigurations
from .models import SOD_EOD_Data

from django import forms
from django.utils import timezone

class TradingConfigurationsForm(forms.ModelForm):
    class Meta:
        model = TradingConfigurations
        fields = '__all__'
        exclude = ['scalping_mode', 'over_trade_status'] 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

        # Fetch the existing TradingConfigurations object
        six_hours_ago = timezone.now() - timezone.timedelta(seconds=1)
        trading_config_exists = TradingConfigurations.objects.filter(last_updated__gte=six_hours_ago)

        if trading_config_exists.exists():
            # Set initial data from the existing record
            self.initial.update(trading_config_exists.first().__dict__)

        else:
            trading_config_exists = TradingConfigurations.objects.order_by('-last_updated').first()
            self.initial.update(trading_config_exists.__dict__)

    def clean(self):
        cleaned_data = super().clean()
        six_hours_ago = timezone.now() - timezone.timedelta(seconds=1)

        trading_config_exists = TradingConfigurations.objects.filter(last_updated__gte=six_hours_ago).exists()

        # if trading_config_exists:
        #     raise forms.ValidationError("Cannot modify the configuration on this day.")

        return cleaned_data


class SOD_DataForm(forms.ModelForm):
    class Meta:
        model = SOD_EOD_Data
        fields = ['opening_balance', 'withdrwal_amount', 'deposit_amount', 'week_no','prev_day_slippage', 'trading_date']


    def __init__(self,  *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add classes to form fields for Bootstrap styling
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

        self.fields['opening_balance'].disabled = True
        self.fields['week_no'].disabled = True
        self.fields['trading_date'].disabled = True
        

        

class EOD_DataForm(forms.ModelForm):
    class Meta:
        model = SOD_EOD_Data
        fields = ['closing_balance', 'withdrwal_amount', 'deposit_amount','day_p_and_l','day_exp_brokerage','day_order_count','notes']


    def __init__(self,  *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add classes to form fields for Bootstrap styling
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

        self.fields['closing_balance'].disabled = True
        self.fields['day_p_and_l'].disabled = True
        self.fields['day_order_count'].disabled = True
        self.fields['day_exp_brokerage'].disabled = True


