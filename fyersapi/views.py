from decimal import Decimal
import json
from django.shortcuts import render
from django.views import View
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect
from account.models import CommonConfig
from fyers_apiv3 import fyersModel
import webbrowser
from django.core.paginator import Paginator
from django.shortcuts import render
from django.views import View
from .models import OpenOrderTempData, TradingData
from django.shortcuts import render
from django.views import View
from django.http import HttpResponse
from .models import TradingData
from django.utils import timezone
from django.db.models import Q
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from .forms import EOD_DataForm, SOD_DataForm, TradingConfigurationsForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
import datetime
from asgiref.sync import sync_to_async
from dhanhq import dhanhq
from django.views.decorators.http import require_GET
from django.shortcuts import redirect
from django.conf import settings



class Brokerconfig(LoginRequiredMixin, View):
    login_url = '/login'
    def get(self, request, *args, **kwargs):
        template = "trading_tool/html/index.html"
        context = {}
        return render(request, template, context)
    


def brokerconnect(request, app=None):
    # Get client_id, secret_key, and redirect_uri from settings.py
    client_id = settings.FYERS_APP_ID
    secret_key = settings.FYERS_SECRET_ID
    redirect_uri = settings.FYERS_REDIRECT_URL + "/dashboard"
    grant_type = "authorization_code"    
    response_type = "code"
    state = "sample_state"

    print('client_idclient_idclient_id', client_id)
    print('secret_keysecret_key', secret_key)
    
    # Create a session model with the provided credentials
    session = fyersModel.SessionModel(
        client_id=client_id,
        secret_key=secret_key,
        redirect_uri=redirect_uri,
        response_type=response_type,
        state=state
    )
    
    # Generate the auth code URL
    response = session.generate_authcode()

    print('redirect_uriredirect_uri', redirect_uri)
    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>', response)
    
    # If 'app' is provided, return the generated URL; otherwise, redirect to it
    if app:
        return response

    return redirect(response)



def get_accese_token(request):
    # return redirect('some_redirect_url')
    client_id = settings.FYERS_APP_ID
    secret_key = settings.FYERS_SECRET_ID
    redirect_uri = settings.FYERS_REDIRECT_URL+"/dashboard"
    response_type = "code" 
    grant_type = "authorization_code"  
    # The authorization code received from Fyers after the user grants access
    auth_code = request.session.get(' ')
    # Create a session object to handle the Fyers API authentication and token generation
    session = fyersModel.SessionModel(
        client_id=client_id,
        secret_key=secret_key, 
        redirect_uri=redirect_uri, 
        response_type=response_type, 
        grant_type=grant_type
    )
    #print("sessionsession", session)
    # Set the authorization code in the session object
    session.set_token(auth_code)
    # Generate the access token using the authorization code
    response = session.generate_token()
    #print("responseresponse", response)
    # #print the response, which should contain the access token and other details
    access_token = response.get('access_token')
    refresh_token = response.get('refresh_token')
    if access_token:
        return access_token

    else:
        return None
        

def get_accese_token_store_session(request):
    # Get client_id and secret_key from settings.py
    client_id = settings.FYERS_APP_ID
    secret_key = settings.FYERS_SECRET_ID
    redirect_uri = settings.FYERS_REDIRECT_URL+"/dashboard"
    response_type = "code" 
    grant_type = "authorization_code"  
    auth_code = request.session.get('auth_code')
    print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!', auth_code)
    # Create a session object to handle the Fyers API authentication and token generation
    session = fyersModel.SessionModel(
        client_id=client_id,
        secret_key=secret_key, 
        redirect_uri=redirect_uri, 
        response_type=response_type, 
        grant_type=grant_type
    )
    # Set the authorization code in the session object
    session.set_token(auth_code)
    # Generate the access token using the authorization code
    response = session.generate_token()
    print('responseresponseresponseresponseresponseresponseresponse', response)
    # #print the response, which should contain the access token and other details
    access_token = response.get('access_token')
    refresh_token = response.get('refresh_token')
    if access_token and refresh_token:
        request.session['access_token'] = access_token
        request.session['refresh_token'] = refresh_token
        obj1, created = CommonConfig.objects.update_or_create(
                param='access_token',
                defaults={"value": access_token}
            )
        obj2, created = CommonConfig.objects.update_or_create(
                    param='refresh_token',
                    defaults={"value": refresh_token}
                )

        print('access_tokenaccess_tokenaccess_token', access_token)
        print('refresh_tokenrefresh_tokenrefresh_tokenrefresh_token', refresh_token)
    else:
        print("access_token or refresh_token missing")
        pass
    # You can redirect to another page or render a template after #printing
    return redirect('dashboard')  # Assuming 'home' is the name of a URL pattern you want to redirect to

def partial_exit_positions(request):
    client_id = settings.FYERS_APP_ID
    access_token = request.session.get('access_token')
    
    if not access_token:
        return redirect('dashboard')
    
    trade_config_data = TradingConfigurations.objects.order_by('-last_updated').only(
        'scalping_mode', 'max_trade_count', 'order_quantity_mode', 'default_order_qty', 
        'over_trade_status', 'scalping_amount_limit', 'capital_limit_per_order'
    ).first()
    
    fyers = fyersModel.FyersModel(client_id=client_id, token=access_token, log_path="")
    order_data = fyers.orderbook()
    
    orders_with_status_6 = [
        {"id": order["id"]} for order in order_data["orderBook"] if order["status"] == 6
    ]
    order_symbol_data = [
        {"symbol": order["symbol"], "qty": order["qty"]} for order in order_data["orderBook"] if order["status"] == 6
    ]
    
    if not order_symbol_data:
        message = "No open positions/ Orders"
        messages.error(request, message)
        return JsonResponse({'message': message})
    
    order_symbol = order_symbol_data[0]['symbol']
    order_qty = order_symbol_data[0]['qty']
    partial_qty = math.ceil(order_qty * 0.5)
    remain_qty = order_qty - partial_qty
    
    if orders_with_status_6:
        order_cancel_response = fyers.cancel_basket_orders(data=orders_with_status_6)
        messages.success(request, order_cancel_response)
    else:
        messages.success(request, "No pending orders to cancel.")
    
    sell_order_data = {
        "symbol": order_symbol,
        "qty": partial_qty,
        "type": 2,  # Market Order
        "side": 2,  # Buy
        "productType": "INTRADAY",
        "validity": "DAY",
        "offlineOrder": False
    }
    
    response = fyers.place_order(data=sell_order_data)
    response["code"] = 1101 
    if response.get("code") == 1101:
        open_order_data = OpenOrderTempData.objects.filter(symbol=order_symbol).first()
        traded_price = open_order_data.average_price
        if remain_qty == 0 :
            OpenOrderTempData.objects.all().delete()
        else:
            open_order_data.quantity = remain_qty
            open_order_data.save()
        
        stoplossConf = trade_config_data.scalping_stoploss if trade_config_data.scalping_mode else trade_config_data.default_stoploss
        default_stoploss = Decimal(stoplossConf)
        stoploss_limit_slippage = Decimal(trade_config_data.stoploss_limit_slippage)
        
        stoploss_price = traded_price - (traded_price * default_stoploss / 100)
        stoploss_price = round(stoploss_price / Decimal(0.05)) * Decimal(0.05)
        stoploss_price = round(stoploss_price, 2)
        
        stoploss_limit = stoploss_price - stoploss_limit_slippage
        stoploss_limit = round(stoploss_limit / Decimal(0.05)) * Decimal(0.05)
        stoploss_limit = round(stoploss_limit, 2)
        
        sl_data = {
            "symbol": order_symbol,
            "qty": remain_qty,
            "type": 4,  # SL-L
            "side": -1,  # Sell
            "productType": "INTRADAY",
            "limitPrice": float(stoploss_limit),
            "stopPrice": float(stoploss_price),
            "validity": "DAY",
            "offlineOrder": False,
        }
        
        stoploss_order_response = fyers.place_order(data=sl_data)
        if stoploss_order_response["code"] == 1101:
            message = "BUY/SL-L Placed Successfully"
            return JsonResponse({'response': message, 'symbol': order_symbol, 'qty': order_qty, 'traded_price': traded_price})
        elif stoploss_order_response["code"] == -99:
            message = "SL-L not Placed, Insufficient Fund"
            return JsonResponse({'response': message})
        else:
            return JsonResponse({'response': stoploss_order_response["message"]})
    
    if 'message' in response:
        message = response['message']
        messages.success(request, message)
        OpenOrderTempData.objects.all().delete()
        return JsonResponse({'message': message, 'code': response['code']})
    else:
        message = "Error: Response format is unexpected"
        messages.error(request, message)
        return JsonResponse({'message': message, 'code': response['code']})


from asgiref.sync import sync_to_async
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404


@csrf_exempt
def close_all_positions(request):
    # confData = TradingConfigurations.objects.order_by('-last_updated').only('active_broker').first()
    active_broker = "FYERS"
    # print('active_brokeractive_brokeractive_broker', confData.active_broker)

    if active_broker == "FYERS":
        client_id = settings.FYERS_APP_ID
        # try :
        #     access_token = request.session.get('access_token')
        # except :
        config = get_object_or_404(CommonConfig, param="access_token")
        # Access the 'value' field
        access_token = config.value
    
        if not access_token:
            return redirect('dashboard')
        
        fyers = fyersModel.FyersModel(client_id=client_id, token=access_token, log_path="")
        order_data = fyers.orderbook()

        order_book = order_data["orderBook"]

        # Create a set of order IDs with status 6
        orders_with_status_6 = {order["id"] for order in order_book if order["status"] == 6}

        # Convert the set to a list of dictionaries if needed
        orders_with_status_6_list = [{"id": order_id} for order_id in orders_with_status_6]

        if orders_with_status_6:
            order_cancel_response = fyers.cancel_basket_orders(data=orders_with_status_6)
            messages.success(request, order_cancel_response)
        else:
            messages.info(request, "No pending orders to cancel.")

        # Exit positions
        data = {
            "segment": [11],
            "side": [1],
            "productType": ["INTRADAY"]
        }
        response = fyers.exit_positions(data=data)

        if 'message' in response:
            message = response['message']
            OpenOrderTempData.objects.all().delete()
            return JsonResponse({'message': message, 'code': response['code']})
        else:
            message = "Error: Response format is unexpected"
            messages.error(request, message)
            return JsonResponse({'message': message, 'code': response.get('code', 'unknown')})
        
    elif active_broker == "DHAN":
        dhan_client_id = settings.DHAN_CLIENTID
        dhan_access_token = settings.DHAN_ACCESS_TOKEN

        dhan = dhanhq(dhan_client_id, dhan_access_token)
        # get Order Listing : Pending 
        orderlist = dhan.get_order_list()
        get_pending_order_data = get_pending_orders_dhan(orderlist)

        # CLOSE ALL PENDING ORDERS
        if get_pending_order_data:
            sl_order_id_list =[]
            for sl_order_data in get_pending_order_data['data']:
                sl_order_id = sl_order_data['orderId']
                sl_order_id_list.append(sl_order_id)

            for id in sl_order_id_list:
                cancel_order_response = dhan.cancel_order(id)

            if cancel_order_response['status'] == 'failure':
                return JsonResponse({'message': 'S-L updation failed !',  'code': '-99'})
            
            close_response = get_position_close_process(dhan)

            if close_response == False:
                return JsonResponse({'message': 'NO Open Positions','code': '-99'})
            
            if close_response['status'] == 'success':
                return JsonResponse({'message': 'SUccessfully Close Positions','code': '-99'})
            
            return JsonResponse({'message': 'Cannot Close Positions',  'code': '-99'})

        else: 
            # GET POSITION AND CLOSE IT 
            close_response = get_position_close_process(dhan)

            if close_response == False:
                return JsonResponse({'message': 'No Open Positions','code': '-99'})
            
            if close_response['status'] == 'success':
                return JsonResponse({'message': 'SUccessfully Close Order','code': '-99'})

            return JsonResponse({'message': 'Cannot Close Positions',  'code': '-99'})
    else:
        return JsonResponse({'message': 'Invalid broker', 'code': '-1'})
    
    
from django.shortcuts import redirect
from django.http import JsonResponse
from django.contrib import messages
from django.conf import settings
@csrf_exempt
def api_close_all_positions(request):
    # Assuming active_broker is fetched from the configuration
    active_broker = "FYERS"

    if active_broker == "FYERS":
        client_id = settings.FYERS_APP_ID
        access_token = request.session.get('access_token')
        
        if not access_token:
            return redirect('dashboard')
        
        fyers = fyersModel.FyersModel(client_id=client_id, token=access_token, log_path="")
        order_data = fyers.orderbook()

        order_book = order_data["orderBook"]

        # Create a set of order IDs with status 6
        orders_with_status_6 = {order["id"] for order in order_book if order["status"] == 6}

        # Convert the set to a list of dictionaries if needed
        orders_with_status_6_list = [{"id": order_id} for order_id in orders_with_status_6]

        if orders_with_status_6:
            order_cancel_response = fyers.cancel_basket_orders(data=orders_with_status_6)
            messages.success(request, order_cancel_response)
        else:
            messages.info(request, "No pending orders to cancel.")

        # Exit positions
        data = {
            "segment": [11],
            "side": [1],
            "productType": ["INTRADAY"]
        }
        response = fyers.exit_positions(data=data)

        if 'message' in response:
            message = response['message']
            OpenOrderTempData.objects.all().delete()
            return JsonResponse({'message': message, 'code': response['code']})
        else:
            message = "Error: Response format is unexpected"
            messages.error(request, message)
            return JsonResponse({'message': message, 'code': response.get('code', 'unknown')})
        
    else:
        return JsonResponse({'message': 'Invalid broker', 'code': '-1'})



def get_position_close_process(dhan):
    open_positions  = dhan.get_positions()
    print("open_positionsopen_positionsopen_positions", open_positions)
    if open_positions['data'] == []:
        return False
    
    else:
        securityId = open_positions['data']['securityId']
        quantity = open_positions['data']['quantity']

        close_response = dhan.place_order(security_id=securityId,  #NiftyPE
                exchange_segment=dhan.NSE_FNO,
                transaction_type=dhan.SELL,
                quantity=quantity,
                order_type=dhan.MARKET,
                product_type=dhan.INTRA,
                price=0)
        
        return close_response

def get_data_instance(request):

    context={}
    template="trading_tool/html/profile_view.html"
    client_id = settings.FYERS_APP_ID
    access_token = request.session.get('access_token')
    if access_token:
        # Initialize the FyersModel instance with your client_id, access_token, and enable async mode
        fyers = fyersModel.FyersModel(client_id=client_id, is_async=False, token=access_token, log_path="")
        # Return the response received from the Fyers API
        return fyers
    else:
        #print("noithing here")
        # return redirect('dashboard')  
        # Handle the case where access_token is not found in the session
        pass
    return None

def get_fyers_data_instance(request):
    context={}
    template="trading_tool/html/profile_view.html"
    client_id = settings.FYERS_APP_ID
    access_token = request.session.get('access_token')
    if access_token:
        # Initialize the FyersModel instance with your client_id, access_token, and enable async mode
        fyers = fyersModel.FyersModel(client_id=client_id, is_async=False, token=access_token, log_path="")
        # Return the response received from the Fyers API
        return fyers
    else:
        #print("noithing here")
        # return redirect('dashboard')  
        # Handle the case where access_token is not found in the session
        pass
    return None


class ProfileView(LoginRequiredMixin, View):
  login_url = '/login'
  def get(self, request):
    client_id = settings.FYERS_APP_ID
    access_token = request.session.get('access_token')

    if access_token:
      fyers = fyersModel.FyersModel(
        client_id=client_id, 
        is_async=False, 
        token=access_token,
        log_path=""
      )
      response = fyers.get_profile()
      context = response
      return render(request, 'trading_tool/html/profile_view.html', context)
    
    else:
      #print("no access token")
      return render(request, 'trading_tool/html/profile_view.html')


from datetime import datetime, date
from django.http import JsonResponse
from .models import TradingConfigurations  # Replace 'myapp' with your actual Django app name

def SOD_Config_Process(request):
    try:
        today = date.today()
        
        # Check if an entry for today already exists
        existing_entry = TradingConfigurations.objects.filter(last_updated__date=today).exists()
        
        if existing_entry:
            # Return a JsonResponse indicating that SOD (Start of Day) for today is already done
            return JsonResponse({'message': f'SOD for {today} already done.'})
        
        # Fetch the latest TradingConfigurations object
        latest_config = TradingConfigurations.objects.order_by('-last_updated').first()

        if latest_config:
            # Create a new entry with over_trade_status set to False and last_updated to current timestamp
            new_config = TradingConfigurations(
                default_stoploss=latest_config.default_stoploss,
                default_order_qty=latest_config.default_order_qty,
                reward_ratio=latest_config.reward_ratio,
                max_loss=latest_config.max_loss,
                max_trade_count=latest_config.max_trade_count,
                capital_limit_per_order=latest_config.capital_limit_per_order,
                capital_usage_limit=latest_config.capital_usage_limit,
                forward_trailing_points=latest_config.forward_trailing_points,
                trailing_to_top_points=latest_config.trailing_to_top_points,
                reverse_trailing_points=latest_config.reverse_trailing_points,
                stoploss_limit_slippage=latest_config.stoploss_limit_slippage,
                last_updated=datetime.now(),  # Set the current timestamp
                averaging_limit=latest_config.averaging_limit,
                order_quantity_mode=latest_config.order_quantity_mode,
                scalping_amount_limit=latest_config.scalping_amount_limit,
                scalping_mode=latest_config.scalping_mode,
                scalping_stoploss=latest_config.scalping_stoploss,
                scalping_ratio=latest_config.scalping_ratio,
                straddle_amount_limit=latest_config.straddle_amount_limit,
                straddle_capital_usage=latest_config.straddle_capital_usage,
                over_trade_status=False,  # Set over_trade_status to False
                averaging_qty=latest_config.averaging_qty,
                active_broker=latest_config.active_broker,
            )

            # Save the new configuration
            new_config.save()
            
            # Return a JsonResponse indicating successful creation of SOD for today
            return JsonResponse({'message': f'SOD for {today} done successfully.'})

    except TradingConfigurations.DoesNotExist:
        # Handle the case where no configurations exist
        pass

    # Return a JsonResponse if there was an issue or no configurations were found
    return JsonResponse({'message': 'Unable to perform SOD operation.'})



from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import SOD_EOD_Data
@csrf_exempt
def fetch_date_data(request):
    if request.method == 'POST':
        date_str = request.POST.get('date')
        
        date_obj = datetime.strptime(date_str, '%d-%m-%Y')
        #print("date_strdate_strdate_str", date_obj)
        
        data_instance = SOD_EOD_Data.objects.filter(trading_date=date_obj).first()
        data_instance = SOD_EOD_Data.objects.filter(trading_date=date_obj).first()
        #print("data_instancedata_instance", data_instance)
        
        if data_instance:
            data = {
                'trading_date': data_instance.trading_date,
                'opening_balance': data_instance.opening_balance,
                'closing_balance': data_instance.closing_balance,
                'day_exp_brokerage': data_instance.day_exp_brokerage,
                'day_order_count': data_instance.day_order_count,
                'day_p_and_l': data_instance.day_p_and_l,
                'actual_expense': data_instance.actual_expense,
                'actual_benefit': data_instance.actual_benefit,
                'notes': data_instance.notes,
       
                # 'some_other_field': data_instance.some_other_field,
                # # Add other fields as necessary
            }
            #print("datadatadata", data)
            return JsonResponse({'data': data}, status=200)
        else:
            return JsonResponse({'error': 'No data found for the given date'}, status=404)

    return JsonResponse({'error': 'Invalid request method'}, status=400)


from django.http import JsonResponse
from django.utils import timezone
from collections import defaultdict
from datetime import timedelta
from .models import SOD_EOD_Data

def daily_candle_overview(request):
    fifteen_days_ago = timezone.now() - timedelta(days=15)
    # Query the database for SOD_EOD_Data objects within the past 15 days
    data_objects = SOD_EOD_Data.objects.filter(trading_date__gte=fifteen_days_ago)
    
    if data_objects.exists():
        # Create a defaultdict to store balance data for each date
        balance_data = defaultdict(list)
        
        # Iterate through the data_objects and collect opening and closing balance data
        for obj in data_objects:
            trading_date = obj.trading_date.strftime('%Y-%m-%d')
            # Append opening balance twice and closing balance twice
            balance_data[trading_date].extend([float(obj.opening_balance), float(obj.opening_balance), float(obj.closing_balance), float(obj.closing_balance)])
        
        # Format the data into the desired format
        formatted_data = []
        for date, balances in balance_data.items():
            print("balancesbalances", balances)
            formatted_data.append({'x': date, 'y': balances})

        print("formatted_dataformatted_data", formatted_data)
        
        return JsonResponse(formatted_data, safe=False)

    else:
        return JsonResponse({'error': 'No data found within the past 15 days'}, status=404)
    


# ---------------------------------------------------------------------------------------------------------------------------

from django.http import JsonResponse
def update_data_instance(request):
    context = {}
    client_id = settings.FYERS_APP_ID
    access_token = request.session.get('access_token')
    total_order_status=0

    if access_token:
        data_instance = get_data_instance(request)
        # fyers = fyersModel.FyersModel(client_id=client_id, is_async=False, token=access_token, log_path="")
        positions_data = data_instance.positions()
        order_data = data_instance.orderbook()
        fund_data = data_instance.funds()
        if "orderBook" in order_data:
            total_order_status = sum(1 for order in order_data["orderBook"] if order["status"] == 2)
        # Process the response and prepare the data
        data = { 'positions': positions_data,
                'total_order_status': total_order_status ,
                'fund_data': fund_data,
                'order_data': order_data
                }  # Modify this according to your response structure
        
        # print("datadatadata", data)
        return JsonResponse(data)
    else:
        return JsonResponse({'error': 'Access token not found'}, status=400)
    
# ---------------------------------------------------------------------------------------------------------------------------

from django.views.generic import TemplateView

class CandleOverviewView(TemplateView):
    template_name = 'trading_tool/html/candle_overview.html'


class EOD_ReportingView(LoginRequiredMixin, FormView):
    login_url = '/login'
    template_name = 'trading_tool/html/eod_form.html'
    form_class = EOD_DataForm
    success_url = reverse_lazy('dashboard')

    def get_initial_data(self):
        initial = super().get_initial()
        # Retrieve slug data from URL parameters
        # Load initial value for week_no
        data_instance = get_data_instance(self.request)
        fund_data = data_instance.funds()
        order_data = data_instance.orderbook()
        total_order_status = sum(1 for order in order_data["orderBook"] if order["status"] == 2)
        total_balance = 0
        realised_profit = 0
        total_order_status = 0  
        confData = TradingConfigurations.objects.order_by('-last_updated').first()
        cost = confData.capital_limit_per_order
        tax = calculate_tax(cost)
        default_brokerage = settings.DEFAULT_BROKERAGE + tax
        # default_brokerage = settings.DEFAULT_BROKERAGE
        exp_brokerage = default_brokerage * total_order_status

        for item in fund_data.get('fund_limit', []):
            if item.get('title') == 'Total Balance':
                total_balance = item.get('equityAmount')
            if item.get('title') == 'Realized Profit and Loss':
                realised_profit = item.get('equityAmount')
                break

        initial['day_exp_brokerage'] = exp_brokerage
        initial['day_order_count'] = total_order_status
        initial['day_p_and_l'] = realised_profit
        initial['closing_balance'] = total_balance
        return initial

    def get_initial(self):
        return self.get_initial_data()

    def form_valid(self, form):
        # Check if a record with the same trading_date already exists
        trading_date = datetime.date.today()
        existing_instance = SOD_EOD_Data.objects.filter(trading_date=trading_date).first()
        #print("existing_instance", existing_instance)
        
        if existing_instance:
            # If a record exists, update the existing instance with the form data
            for field in form.Meta.fields:
                setattr(existing_instance, field, form.cleaned_data[field])
            existing_instance.save()
            return JsonResponse({'success': 'Form data updated successfully.'})
        else:
            # If no record exists, save the form data as a new instance
            form.save()
            return JsonResponse({'success': 'Form submitted successfully.'})

    def form_invalid(self, form):
        errors = form.errors.as_json()
        return JsonResponse({'errors': errors}, status=400)


import calendar
from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.conf import settings  
import datetime


class TradingCalenderView(LoginRequiredMixin, View):
    login_url = '/login'

    def get_first_last_dates(self, year, month):
        first_date = datetime(year, month, 1).strftime('%Y-%m-%d')
        last_date = (datetime(year, month, calendar.monthrange(year, month)[1])
                     .strftime('%Y-%m-%d'))
        return first_date, last_date

    def get(self, request):
        client_id = settings.FYERS_APP_ID
        access_token = request.session.get('access_token')

        if access_token:
            fyers = fyersModel.FyersModel(
                client_id=client_id, 
                is_async=False, 
                token=access_token,
                log_path=""
            )
            response = fyers.get_profile()

            # Get current month calendar
            now = datetime.now()
            year = now.year
            month = now.month
            cal = calendar.monthcalendar(year, month)
            month_name = calendar.month_name[month]
            first_date, last_date = self.get_first_last_dates(year, month)

            date_wise_data = SOD_EOD_Data.objects.filter(trading_date=now).first()



            if request.is_ajax():
                # If the request is AJAX and it's for the previous month data
                year = request.GET.get('year')
                month = request.GET.get('month')
                if  'prev_month' in request.GET:
                    year, month = self.calculate_previous_month(int(year), int(month))  # Function to calculate the previous month
                elif 'next_month' in request.GET:
                    year, month = self.calculate_next_month(int(year), int(month))  # Function to calculate the previous month
                elif 'current_month' in request.GET:
                    year = int(year)
                    month = int(month)
                    # year, month = self.calculate_next_month(int(year), int(month))  # Function to calculate the previous month
                print('yearyearyearyearyearyearyearyearyear', year, type(year))
                print('month', month, type(month))

                cal = calendar.monthcalendar(year, month)
                month_name = calendar.month_name[month]
                first_date, last_date = self.get_first_last_dates(year, month)
                # Iterate over each week in the calendar data
                for week in cal:
                    # Check if the first day of the week is valid
                    if week[6]  != 0:
                        # If the first day is None, indicating days outside the month, find the first valid day
                        for day in week:
                            if day  != 0:
                                week_number = self.get_week_of_year(year, month, day)
                                week.append(week_number)
                                break
                    else:
                        # Calculate week number for the first day of the week
                        week_number = self.get_week_of_year(year, month, week[0])
                        # Append week number to the week list
                        week.append(week_number)

                profit_data = SOD_EOD_Data.objects.filter(trading_date__range=[first_date, last_date])
                profit_data_dict = {entry['trading_date'].strftime('%d-%m-%Y'): entry['day_p_and_l'] for entry in profit_data.values('trading_date', 'day_p_and_l')}            
                #print("profit_data_dict", profit_data_dict)

                combined_list = []
                for row in cal:
                    combined_row = []
                    counter=1
                    for i, item in enumerate(row):
                        limit = len(row)
                        if i == limit:
                            combined_row.append(item)  
                            #print("combined_row", combined_row)
                            # Append the last item as is
                        elif isinstance(item, int):
                                date_key = f"{item:02d}-{month:02d}-{year}"  # Construct the date dynamically
                                if date_key in profit_data_dict:
                                    #print('date_key', date_key, item)
                                    combined_row.append({counter:[item ,float(profit_data_dict[date_key])]})  # Change Decimal to float
                                else:
                                    #print('date_key11', date_key, item)
                                    combined_row.append({counter:[item , 0.00]})  # Change Decimal to float
                        else:
                            #print('date_key12', date_key, item)
                            #print("ppppppppp", i, item)
                            combined_row.append(item)
                        counter +=1
                    combined_list.append(combined_row)
                    for sublist in combined_list:
                        sublist_sum = 0
                        for d in sublist:
                            for key, value in d.items():
                                if key in range(1, 6):  # Check if the key is between 1 and 5
                                    sublist_sum += value[1]  # Add the second element of the value
                                if key == 8:
                                    value[1] = sublist_sum

                    #print("combined_listcombined_list", combined_list)

                return JsonResponse({'calendar': combined_list, 'month_name': month_name, 'month': month, 'year': year, 'first_date': first_date, 'last_date': last_date, 'now' : now})
            


            
            # Iterate over each week in the calendar data
            for week in cal:
                # Check if the first day of the week is valid
                if week[6]  != 0:
                    # If the first day is None, indicating days outside the month, find the first valid day
                    for day in week:
                        # sod_eod_data = SOD_EOD_Data.object.filter()
                        if day  != 0:
                            week_number = self.get_week_of_year(year, month, day)
                            week.append(week_number)
                            break
                else:
                    # Calculate week number for the first day of the week
                    week_number = self.get_week_of_year(year, month, week[0])
                    # Append week number to the week list
                    week.append(week_number)

            profit_data = SOD_EOD_Data.objects.filter(trading_date__range=[first_date, last_date])
            profit_data_dict = {entry['trading_date'].strftime('%d-%m-%Y'): entry['day_p_and_l'] for entry in profit_data.values('trading_date', 'day_p_and_l')}            
            #print("profit_data_dict", profit_data_dict)

            combined_list = []
            for row in cal:
                combined_row = []
                counter=1
                for i, item in enumerate(row):
                    limit = len(row)
                    if i == limit:
                        combined_row.append(item)  
                        #print("combined_row", combined_row)
                        # Append the last item as is
                    elif isinstance(item, int):
                            date_key = f"{item:02d}-{month:02d}-{year}"  # Construct the date dynamically
                            if date_key in profit_data_dict:
                                #print('date_key', date_key, item)
                                combined_row.append({counter:[item ,float(profit_data_dict[date_key])]})  # Change Decimal to float
                            else:
                                #print('date_key11', date_key, item)
                                combined_row.append({counter:[item , 0.00]})  # Change Decimal to float
                    else:
                        #print('date_key12', date_key, item)
                        #print("ppppppppp", i, item)
                        combined_row.append(item)
                    counter +=1
                combined_list.append(combined_row)
                for sublist in combined_list:
                    sublist_sum = 0
                    for d in sublist:
                        for key, value in d.items():
                            if key in range(1, 6):  # Check if the key is between 1 and 5
                                sublist_sum += value[1]  # Add the second element of the value
                            if key == 8:
                                value[1] = sublist_sum


                






            # for date, profit in profit_data_dict.items():
            #     day = int(date.split('-')[0])
            #     for row in cal:
            #         if day in row[:-1]:  # Exclude the last element of the sublist
            #             index = row.index(day)
            #             row[index] = f"{day}:{profit}"




            context = {
                'calendar': combined_list, 
                'month_name': month_name,
                'month': month,
                'year': year,
                'first_date': first_date,
                'last_date': last_date,
                'now' : now,
                'now_date': now.day,
                'now_month': now.month,
                'now_year': now.year,
                'date_wise_data' : date_wise_data,
                'profit_data_dict': profit_data_dict
            }
            return render(request, 'trading_tool/html/calender_view.html', context)
        
        else:
            #print("no access token")
            return render(request, 'trading_tool/html/calender_view.html')

    def calculate_next_month(self, year, month):
        # Calculate the next month
        month += 1
        if month > 12:
            # If the current month is December, go to the next year and set the month to January
            year += 1
            month = 1
        return year, month
    
    def calculate_previous_month(self, year, month):
        # Calculate the previous month
        month -= 1
        if month == 0:
            # If the current month is January, go to the previous year
            year -= 1
            month = 12

        return year, month

    def get_week_of_year(self, year, month, day):
        # Calculate the nth week of the year if the day is valid for the month
        if 1 <= day <= calendar.monthrange(year, month)[1]:
            week_number = datetime(year, month, day).isocalendar()[1]
            return week_number
        else:
            return None  # Return None if the day is outside the valid range for the month


from django.http import JsonResponse
class OrderHistory(LoginRequiredMixin, View):
    login_url = '/login'

    def get(self, request):
        context = {}
        data_instance = get_data_instance(request)
        order_data = data_instance.orderbook()
        page_count = 10

        # Ensure order_data is a list or a queryset
        if not isinstance(order_data, list):
            # If order_data is not a list, assume it's a dictionary and extract the 'orderBook' key
            order_data = order_data.get('orderBook', [])
            order_data = sorted(order_data, key=lambda x: x['slNo'], reverse=True)

            # Map status values to their descriptions
            for order in order_data:
                order['status_description'] = settings.STATUS_DESCRIPTIONS.get(order.get('status', 'Unknown'))

        if request.is_ajax():
            load_more = request.GET.get('load_more', None)
            if load_more:
                page_count=200


        paginator = Paginator(order_data, page_count)  # Show 20 items per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        if request.is_ajax():
            # If the request is AJAX, fetch the filter value and filter the queryset

            status_filter = request.GET.get('status', None)  # Assuming AJAX passes 'status' parameter for filtering
            print("status_filterstatus_filter", status_filter)
         
            
            # Get the current page's data
            current_page_data = list(page_obj)
            filtered_data=[]

            print("current_page_datacurrent_page_data", current_page_data)

            # Filter the current page's data based on the status
            if status_filter:
                filtered_data = [order for order in current_page_data if order.get('status') == int(status_filter)]
                print("filtered_datafiltered_datafiltered_data", filtered_data)
            else:
                filtered_data = current_page_data

            # Create a new paginator for the filtered data
            filtered_paginator = Paginator(filtered_data, page_count )
            filtered_page_number = request.GET.get('page')
            filtered_page_obj = filtered_paginator.get_page(filtered_page_number)

            # Return the filtered data as JSON response
            return render(request, 'trading_tool/html/order_ajaxtemp.html', {'order_history_data': filtered_page_obj})

        # Otherwise, return the entire rendered page
        context['order_history_data'] = page_obj
        return render(request, 'trading_tool/html/order_history.html', context)
    

from django.http import JsonResponse
class TransactionHistory(LoginRequiredMixin, View):
    login_url = '/login'

    def get(self, request):
        context = {}
        get_transaction_data =SOD_EOD_Data.objects.filter(
                                    Q(withdrwal_amount__gt=0) | Q(withdrwal_amount__lt=0) |
                                    Q(deposit_amount__gt=0) | Q(deposit_amount__lt=0)
                                ).order_by('-trading_date')
        context['get_transaction_data'] = get_transaction_data
        return render(request, 'trading_tool/html/transaction_history.html', context)


class OptionChainView(View):
    # satheesh
    # login_url = '/login'

    def get(self, request, slug):
        context = {}
        template = 'trading_tool/html/optionchainview.html'
        dhan_client_id = settings.DHAN_CLIENTID
        dhan_access_token = settings.DHAN_ACCESS_TOKEN
        dhan = dhanhq(dhan_client_id,dhan_access_token)
        orderlist = dhan.get_order_list()
        data_instance = get_data_instance(request)
        conf_data = TradingConfigurations.objects.order_by('-last_updated').first()
        active_broker = conf_data.active_broker
        fund_data = data_instance.funds()
        print("fund_datafund_data", fund_data)

        for item in fund_data.get('fund_limit', []):
            if item.get('title') == 'Total Balance':
                total_account_balance = item.get('equityAmount')
            if item.get('title') == 'Realized Profit and Loss':
                realised_profit = item.get('equityAmount')
                break

        print("Total Balance Equity Amount:", total_account_balance)
        print("Realized Profit and Loss Equity Amount:", realised_profit)

        forward_trailing_points = conf_data.forward_trailing_points
        reverse_trailing_points = conf_data.reverse_trailing_points
        scalping_mode = conf_data.scalping_mode
        cost = conf_data.scalping_amount_limit if scalping_mode else conf_data.capital_limit_per_order
        stoploss_percentage = conf_data.scalping_stoploss if scalping_mode else conf_data.default_stoploss
        exchange = "BSE:" if slug == "SENSEX" else "NSE:"

        data = {"symbol": f"{exchange}{slug}-INDEX", "strikecount": 1}
        print('datadata', data)

        try:
            expiry_response = data_instance.optionchain(data=data)
            if active_broker == "FYERS":
                order_data = data_instance.orderbook()
                total_order_status = sum(1 for order in order_data.get("orderBook", []) if order["status"] == 2)
                positions_data = data_instance.positions()
                realized_pl = float(positions_data['overall']['pl_realized'])
                
            elif  active_broker == "DHAN":
                total_order_status = get_traded_order_count_dhan(orderlist) 
                positions_data = dhan.get_positions()
                print("positions_datapositions_datapositions_datapositions_data", positions_data)
                if not positions_data['data'] == []:
                    realized_pl = float(positions_data['data']['realizedProfit'])
                else:
                    realized_pl = 0

            tax = calculate_tax(cost)
            default_brokerage = settings.DEFAULT_BROKERAGE + tax
            exp_brokerage = default_brokerage * total_order_status
            trading_config = TradingConfigurations.objects.order_by('-last_updated').first()
            order_limit = trading_config.max_trade_count
            exp_brokerage_limit = order_limit * default_brokerage

            first_expiry_ts = expiry_response['data']['expiryData'][0]['expiry']
            first_expiry_date = expiry_response['data']['expiryData'][0]['date']
        except (KeyError, AttributeError, IndexError) as e:
            error_message = f'Error occurred: {str(e)}'
            messages.error(request, error_message)
            return redirect('login')

        options_data = {"symbol": f"{exchange}{slug}-INDEX", "strikecount": 4, "timestamp": first_expiry_ts}
        print("-------------------------------------------------------------")
        print("options_dataoptions_dataoptions_dataoptions_data", options_data)
        print("-------------------------------------------------------------")

        try:
            response = data_instance.optionchain(data=options_data)
            print("-------------------------------------------------------------")
            print("responseresponseresponseresponse", response)
            print("-------------------------------------------------------------")
        except AttributeError as e:
            error_message = f'Error occurred while fetching options data: {str(e)}'
            messages.error(request, error_message)
            return render(request, template, context)

        pe_options = [option for option in response['data']['optionsChain'] if option['option_type'] == 'PE']
        pe_options_sorted = sorted(pe_options, key=lambda x: x['strike_price'], reverse=True)

        for index, option in enumerate(pe_options_sorted, start=1):
            option['serial_number'] = index
            option['lot_cost'] = int(option['ltp']) * get_default_lotsize(slug)

        ce_options = [option for option in response['data']['optionsChain'] if option['option_type'] == 'CE']
        ce_options_sorted = sorted(ce_options, key=lambda x: x['strike_price'])

        for index, option in enumerate(ce_options_sorted, start=1):
            option['serial_number'] = index
            option['lot_cost'] = int(option['ltp']) * get_default_lotsize(slug)

        actual_profit = round(realized_pl - float(exp_brokerage), 2)
        reward_ratio = conf_data.reward_ratio
        exp_loss = (cost * stoploss_percentage) / 100
        exp_profit_percentage = stoploss_percentage * reward_ratio
        exp_profit = (cost * exp_profit_percentage) / 100

        day_max_loss = -conf_data.max_loss
        super_trader_threshold = exp_brokerage_limit * reward_ratio * 2
        
        dhan_client_id = settings.DHAN_CLIENTID
        dhan_access_token = settings.DHAN_ACCESS_TOKEN
        
        try:
            dhan = dhanhq(dhan_client_id, dhan_access_token)
            dhan_fund = dhan.get_fund_limits()
        except AttributeError as e:
            dhan_fund = {'code': -1, 'message': f'Error occurred: {str(e)}', 's': 'error'}

        # max_serial_number = len(pe_options_sorted) * 2 - 1
        # atm_index = (max_serial_number // 2) + 1
        
        remaining_orders = order_limit - total_order_status
        progress_percentage = (remaining_orders / order_limit) * 100
        progress_percentage = round(progress_percentage, 1)



        print("total_account_balance", total_account_balance)

        
        
        
        
        

        atm_index = len(pe_options_sorted) // 2  # Calculate the ATM index
        context.update({
            'total_account_balance': total_account_balance,
            'access_token': request.session.get('access_token'),
            'forward_trailing_points': forward_trailing_points,
            'reverse_trailing_points': reverse_trailing_points,
            'ce_options_with_serial': ce_options_sorted,
            'pe_options_with_serial': pe_options_sorted,
            # 'max_serial_number': max_serial_number,
            'atm_index': atm_index,
            'expiry_response': first_expiry_date,
            'realized_pl': realized_pl,
            'order_limit': order_limit,
            'exp_brokerage_limit': exp_brokerage_limit,
            'day_exp_profit': exp_brokerage_limit * reward_ratio,
            'exp_loss': exp_loss,
            'day_max_loss': day_max_loss,
            'day_max_loss_end': -(exp_brokerage_limit * reward_ratio),
            'exp_profit': exp_profit,
            'super_trader_threshold': super_trader_threshold,
            'total_order_status': total_order_status,
            'day_exp_brokerage': exp_brokerage,
            'actual_profit': actual_profit,
            'options_data': response,
            'straddle_capital' : conf_data.straddle_capital_usage*2,
            'straddle_amount_limit' : conf_data.straddle_amount_limit,
            'active_broker': active_broker,
            # 'dhan_fund' : dhan_fund['data']['availabelBalance'],
            'progress_percentage' : progress_percentage
        })
        return render(request, template, context)

def calculate_tax(cost):
    a = 0.000732
    b = 3.962
    tax = a * cost + b
    return tax

def update_latest_data(request):
    data_instance = get_data_instance(request)

    positions = data_instance.positions()
    TradingData.objects.update_or_create(
        category='POSITIONS',
        defaults={'data': positions, 'last_updated': timezone.now()}
    )

    orders = data_instance.orderbook()
    TradingData.objects.update_or_create(
        category='ORDERS',
        defaults={'data': orders, 'last_updated': timezone.now()}
    )

    funds = data_instance.funds()
    TradingData.objects.update_or_create(
        category='FUNDS',
        defaults={'data': funds, 'last_updated': timezone.now()}
    )

    return HttpResponse('Data saved')

   
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic.edit import FormView
from .forms import TradingConfigurationsForm
from .models import TradingConfigurations

from django.http import JsonResponse
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from .forms import TradingConfigurationsForm
from .models import TradingConfigurations
from django.utils import timezone

from django.utils import timezone
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from django.http import JsonResponse
from .forms import TradingConfigurationsForm
from .models import TradingConfigurations

class ConfigureTradingView(LoginRequiredMixin, FormView):
    login_url = '/login'
    template_name = 'trading_tool/html/configure_trading.html'
    form_class = TradingConfigurationsForm
    success_url = reverse_lazy('dashboard')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        six_hours_ago = timezone.now() - timezone.timedelta(seconds=1)
        trading_config_exists = TradingConfigurations.objects.filter(last_updated__gte=six_hours_ago)
        if trading_config_exists.exists():
            kwargs['instance'] = trading_config_exists.first()
        else:
            kwargs['instance'] = TradingConfigurations()

        return kwargs

    def form_valid(self, form):
        six_hours_ago = timezone.now() - timezone.timedelta(seconds=1)
        trading_config_exists = TradingConfigurations.objects.filter(last_updated__gte=six_hours_ago)
        if trading_config_exists.exists():
            return JsonResponse({'error': True})
        else:
            trading_config = form.save(commit=False)
            # Calculate scalping_amount_limit
            trading_config.scalping_amount_limit =  trading_config.capital_limit_per_order / trading_config.scalping_ratio
            trading_config.scalping_stoploss = trading_config.scalping_ratio * trading_config.default_stoploss
            form.save()
        return JsonResponse({'success': True})

    def form_invalid(self, form):
        errors = form.errors.as_json()
        return JsonResponse({'errors': errors}, status=400)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['latest_configurations'] = TradingConfigurations.objects.all().order_by('-last_updated')[:1]  # Modify the query as needed
        return context

def get_default_lotsize(index):
    if index == 'MIDCPNIFTY':
        return 50
    elif index == 'FINNIFTY':
        return 25
    elif index == 'NIFTYBANK':
        return 15
    elif index == 'NIFTY50':
        return 25
    elif index == 'SENSEX':
        return 10
    else:
        return False

from asgiref.sync import sync_to_async
from decimal import Decimal
from django.http import JsonResponse
from django.db.models import Q
from .models import TradingConfigurations, OpenOrderTempData
from rest_framework.decorators import api_view

async def instantBuyOrderWithSL(request):
    if request.method == 'POST':
        # Retrieve data from POST request
        der_symbol = request.POST.get('der_symbol')
        ex_symbol1 = request.POST.get('ex_symbol1')
        ltp = Decimal(request.POST.get('ltp'))

        # Get necessary instances and configurations
        # data_instance = await sync_to_async(get_fyers_data_instance)(request)
        # Get necessary instances and configurations
        data_instance = await sync_to_async(get_fyers_data_instance)(request)
        dhan_client_id = settings.DHAN_CLIENTID
        dhan_access_token = settings.DHAN_ACCESS_TOKEN
        dhan = dhanhq(dhan_client_id,dhan_access_token)

        trade_config_data = await sync_to_async(
            lambda: TradingConfigurations.objects.order_by('-last_updated').only(
                'scalping_mode', 'max_trade_count', 'order_quantity_mode', 'default_order_qty', 'over_trade_status','active_broker',
                'scalping_amount_limit', 'capital_limit_per_order', 'scalping_stoploss', 'default_stoploss', 'stoploss_limit_slippage','averaging_qty'
            ).first()
        )()
        
        # Early exit if trade configuration is not found
        if not trade_config_data:
            return JsonResponse({'message': "Trading configuration not found"})

        get_lot_count = await sync_to_async(get_default_lotsize)(ex_symbol1)

        # Check if max order count limit is reached
        if trade_config_data.over_trade_status:
            if trade_config_data.active_broker == 'DHAN':
                kill_status_response = activate_kill_switch()
                print("kill_status_responsekill_status_response", kill_status_response)
                return JsonResponse({'message': "Max Trade Reached ,"+ kill_status_response })
                
            return JsonResponse({'message': "Max Order count limit Reached"})

        # Check if there are existing orders for different symbols
        tempDatainstance = await sync_to_async(OpenOrderTempData.objects.filter(~Q(symbol=der_symbol)).first)()
        tempDatainstance1 = await sync_to_async(OpenOrderTempData.objects.filter(Q(symbol=der_symbol)).first)()

        if tempDatainstance:
            return JsonResponse({'message': "Unable to place another Symbol Order Now."})

        # Calculate order quantity based on mode
        if trade_config_data.order_quantity_mode == "MANUAL":
            if tempDatainstance1:
                config_qty = trade_config_data.averaging_qty
            else:
                config_qty = trade_config_data.default_order_qty
            order_qty = config_qty * get_lot_count

        elif trade_config_data.order_quantity_mode == "AUTOMATIC":
            limit_amount = (trade_config_data.scalping_amount_limit if trade_config_data.scalping_mode
                            else trade_config_data.capital_limit_per_order)
            per_lot_expense = ltp * get_lot_count
            lotqty = Decimal(limit_amount) // per_lot_expense
            order_qty = int(lotqty * get_lot_count)
            if order_qty == 0:
                return JsonResponse({'message': "Amount Usage Limit Reached"})
        # Example conditional logic for different APIs
        if trade_config_data.active_broker == 'FYERS':
            # Place order
            order_data = {
                "symbol": der_symbol,
                "qty": order_qty,
                "type": 2,  # Market Order
                "side": 1,  # Buy
                "productType": "INTRADAY",
                "validity": "DAY",
                "offlineOrder": False
            }

            response = await sync_to_async(data_instance.place_order)(data=order_data)
            if settings.TEST_MODE == True:
                response['code'] = 1101
            

            if response.get("code") == 1101:
                allOrderData = await sync_to_async(data_instance.orderbook)()
                total_order_count = sum(1 for order in allOrderData.get("orderBook", []) if order["status"] == 2)
                # Check if max order count limit is reached
                if total_order_count >= trade_config_data.max_trade_count:
                    await sync_to_async(TradingConfigurations.objects.order_by('-last_updated').update)(over_trade_status=True)

                order_with_status_6 = next(
                    (order for order in allOrderData.get("orderBook", []) if order['status'] == 6 and order["symbol"] == der_symbol),
                    None
                )  
                if order_with_status_6:
                    exst_qty = order_with_status_6['qty']
                    new_qty = order_qty + exst_qty
                    total_order_expense = new_qty * ltp
                    ext_total_order_expense = Decimal(tempDatainstance1.order_total) + total_order_expense
                    average_price = ext_total_order_expense / new_qty
                    
                    sl_price = tempDatainstance1.sl_price
                    exp_loss = (Decimal(average_price) - Decimal(sl_price)) * Decimal(new_qty)
                    is_averaged = tempDatainstance1.is_averaged + 1

                    # Update the attributes directly
                    tempDatainstance1.order_total = ext_total_order_expense
                    tempDatainstance1.premium_price = ltp
                    tempDatainstance1.quantity = new_qty
                    tempDatainstance1.average_price = average_price
                    tempDatainstance1.exp_loss = exp_loss
                    tempDatainstance1.is_averaged = is_averaged

                    # Save the changes to the database asynchronously
                    await sync_to_async(tempDatainstance1.save)()
                    modify_data = {"id": order_with_status_6["id"], "type": 4, "qty": new_qty}
                    print('modify_datamodify_data', modify_data)
                    modify_response = await sync_to_async(data_instance.modify_order)(data=modify_data)
                    return JsonResponse({'message': modify_response["message"]})

                else:
                    buy_order_id = response["id"]
                    buy_order_data = {"id": buy_order_id}
                    order_details = (await sync_to_async(data_instance.orderbook)(data=buy_order_data))["orderBook"][0]
                    traded_price = Decimal(order_details["tradedPrice"])
                    if settings.TEST_MODE == True:
                        traded_price = 200

                    stoplossConf = trade_config_data.scalping_stoploss if trade_config_data.scalping_mode else trade_config_data.default_stoploss
                    default_stoploss = Decimal(stoplossConf)
                    stoploss_limit_slippage = Decimal(trade_config_data.stoploss_limit_slippage)

                    stoploss_price = traded_price - (traded_price * default_stoploss / 100)
                    stoploss_price = round(stoploss_price / Decimal(0.05)) * Decimal(0.05)
                    stoploss_price = round(stoploss_price, 2)
                    stoploss_limit = stoploss_price - stoploss_limit_slippage
                    stoploss_limit = round(stoploss_limit / Decimal(0.05)) * Decimal(0.05)
                    stoploss_limit = round(stoploss_limit, 2)

                    sl_data = {
                        "symbol": der_symbol,
                        "qty": order_qty,
                        "type": 4,  # SL-L Order
                        "side": -1,  # Sell
                        "productType": "INTRADAY",
                        "limitPrice": float(stoploss_limit),
                        "stopPrice": float(stoploss_price),
                        "validity": "DAY",
                        "offlineOrder": False,
                    }

                    stoploss_order_response = await sync_to_async(data_instance.place_order)(data=sl_data)
                    print('stoploss_order_responsestoploss_order_response', stoploss_order_response)
                    total_purchase_value = traded_price * order_qty
                    sl_price = stoploss_price
                    exp_loss = (traded_price - sl_price) * order_qty
                    if settings.TEST_MODE == True:
                        stoploss_order_response["code"] = 1101

                    if stoploss_order_response["code"] == 1101:
                        await sync_to_async(OpenOrderTempData.objects.create)(
                            symbol=der_symbol,
                            order_total=total_purchase_value,
                            premium_price=traded_price,
                            average_price=traded_price,
                            quantity=order_qty,
                            sl_price=sl_price,
                            exp_loss=exp_loss,
                            is_averaged=0
                        )
                        message = "BUY/SL-L Placed Successfully"
                        return JsonResponse({'message': message, 'symbol': der_symbol, 'qty': order_qty, 'traded_price': traded_price})
                    elif stoploss_order_response["code"] == -99:
                        message = "SL-L not Placed, Insufficient Fund"
                        return JsonResponse({'message': message})
                    else:
                        return JsonResponse({'message': stoploss_order_response["message"]})
            elif response["code"] == -99:
                return JsonResponse({'message': response['message'], 'symbol': der_symbol, 'code': response["code"]})
            else:
                return JsonResponse({'message': response["message"]})
        elif trade_config_data.active_broker == 'DHAN':

            orderlist = dhan.get_order_list()
            print('orderlistorderlistorderlist', orderlist)

            # Dhan API specific logic
            
            # print('der_symbol', der_symbol)
            # print('ex_symbol1', ex_symbol1)
            # print('ltp', ltp)
            formated_der_symbol , formatted_expiry_date = convert_derivative_symbol(der_symbol, ex_symbol1)
            
            csv_result = search_csv(formated_der_symbol , formatted_expiry_date)
            print('*********************************************************************************', csv_result)
            security_id = csv_result[0]['SEM_SMST_SECURITY_ID']
            print('*********************************************************************************', security_id)

            # Place an order for NSE Futures & Options
            buy_response = dhan.place_order(security_id=security_id,  #NiftyPE
                exchange_segment=dhan.NSE_FNO,
                transaction_type=dhan.BUY,
                quantity=order_qty,
                order_type=dhan.MARKET,
                product_type=dhan.INTRA,
                price=0,
                validity= dhan.DAY,
                )
            
            order_id = buy_response['data']['orderId']
            print("order_idorder_idorder_id", order_id)
            buy_order_data = dhan.get_order_by_id(order_id)
            print("buy_order_databuy_order_databuy_order_data", buy_order_data['data']['orderStatus'])

            if buy_order_data['data']['orderStatus'] == 'REJECTED':
                return JsonResponse({'message': buy_order_data['data']['omsErrorDescription'], 'symbol': der_symbol, 'code': '-99'})

            if buy_response['status'] == 'failure':
                return JsonResponse({'message': buy_response['remarks']['message'], 'symbol': der_symbol, 'code': '-99'})
            
            elif buy_order_data['data']['orderStatus'] == 'TRADED':
                order_id = buy_response['data']['orderId'],
                status = buy_response['data']['orderStatus'],
                quantity = buy_response['data']['quantity'],
                price = buy_response['data']['price'],
                triggerPrice = buy_response['data']['triggerPrice'],
                get_pending_order_data = get_pending_orders_dhan(orderlist)
                traded_order_count = get_traded_order_count_dhan(orderlist)            
                if traded_order_count >= trade_config_data.max_trade_count:
                    await sync_to_async(TradingConfigurations.objects.order_by('-last_updated').update)(over_trade_status=True)

                if get_pending_order_data:
                    sl_order_id = get_pending_order_data['data']['orderId']
                    sl_order_qty = get_pending_order_data['data']['quantity']
                    updated_qty = sl_order_qty + order_qty
                    sl_updated_response = dhan.modify_order(
                        order_id = sl_order_id,
                        order_type = dhan.SL,
                        leg_name = '',
                        price = price,
                        triggerPrice = triggerPrice,
                        quantity = updated_qty,
                        validity = dhan.DAY
                    )
                    if sl_updated_response['status'] == 'failure':
                        return JsonResponse({'message': 'S-L updation failed !', 'symbol': der_symbol, 'code': '-99'})

                    elif sl_updated_response['status'] == 'success':
                        total_order_expense = updated_qty * ltp
                        ext_total_order_expense = Decimal(tempDatainstance1.order_total) + total_order_expense
                        average_price = ext_total_order_expense / new_qty
                        
                        sl_price = tempDatainstance1.sl_price
                        exp_loss = (Decimal(average_price) - Decimal(sl_price)) * Decimal(new_qty)
                        is_averaged = tempDatainstance1.is_averaged + 1

                        # Update the attributes directly
                        tempDatainstance1.order_total = ext_total_order_expense
                        tempDatainstance1.premium_price = ltp
                        tempDatainstance1.quantity = new_qty
                        tempDatainstance1.average_price = average_price
                        tempDatainstance1.exp_loss = exp_loss
                        tempDatainstance1.is_averaged = is_averaged

                        # Save the changes to the database asynchronously
                        await sync_to_async(tempDatainstance1.save)()

                        message = "BUY/SL-L Placed Successfully"
                        return JsonResponse({'message': message, 'symbol': der_symbol,})

                if not get_pending_order_data and status == 'TRANSIT' :
                    buy_order_data = dhan.get_order_by_id(order_id)
                    print("buy_order_databuy_order_databuy_order_data", buy_order_data)
                    traded_price = Decimal(buy_order_data['data']['price'])
                    stoplossConf = trade_config_data.scalping_stoploss if trade_config_data.scalping_mode else trade_config_data.default_stoploss
                    default_stoploss = Decimal(stoplossConf)
                    stoploss_limit_slippage = Decimal(trade_config_data.stoploss_limit_slippage)

                    stoploss_price = traded_price - (traded_price * default_stoploss / 100)
                    stoploss_price = round(stoploss_price / Decimal(0.05)) * Decimal(0.05)
                    stoploss_price = round(stoploss_price, 2)
                    stoploss_limit = stoploss_price - stoploss_limit_slippage
                    stoploss_limit = round(stoploss_limit / Decimal(0.05)) * Decimal(0.05)
                    stoploss_limit = round(stoploss_limit, 2)

                    # Place an order for NSE Futures & Options SL ORDER
                    sl_response = dhan.place_order(security_id=security_id,  #NiftyPE
                        exchange_segment=dhan.NSE_FNO,
                        transaction_type=dhan.SELL,
                        quantity=quantity,
                        order_type=dhan.SL,
                        product_type=dhan.INTRA,
                        price=stoploss_limit,
                        triggerPrice=stoploss_price,
                        validity= dhan.DAY,
                        )
                    
                    print('buy_responsebuy_responsebuy_response', sl_response)
                    order_id = sl_response['data']['orderId']
                    print("order_idorder_idorder_id", order_id)
                    sl_order_data = dhan.get_order_by_id(order_id)
                    print("sl_order_datasl_order_datasl_order_data", sl_order_data['data']['orderStatus'])

                    if sl_order_data['data']['orderStatus'] == 'REJECTED':
                        return JsonResponse({'message': sl_order_data['data']['omsErrorDescription'], 'symbol': der_symbol, 'code': '-99'})
                        
                    if sl_response['status'] == 'failure':
                        return JsonResponse({'message': 'S-L order not placed !', 'symbol': der_symbol, 'code': '-99'})
                    
                    elif sl_order_data['data']['orderStatus'] == 'TRADED':
                        total_purchase_value = traded_price * order_qty
                        sl_price = stoploss_price
                        exp_loss = (traded_price - sl_price) * order_qty
                        await sync_to_async(OpenOrderTempData.objects.create)(
                            symbol=der_symbol,
                            order_total=total_purchase_value,
                            premium_price=traded_price,
                            average_price=traded_price,
                            quantity=order_qty,
                            sl_price=sl_price,
                            exp_loss=exp_loss,
                            is_averaged=0
                        )
                        message = "BUY/SL-L Placed Successfully"
                        return JsonResponse({'message': message, 'symbol': der_symbol, 'qty': quantity, 'traded_price': traded_price})

            message = "Some Error Occurred Before Execution"
            return JsonResponse({'message': message})
        
    else:
        message = "Some Error Occurred Before Execution"
        return JsonResponse({'message': message})


def get_pending_orders_dhan(response):
    # Check if the response contains 'data'
    if 'data' not in response:
        return None

    # Filter orders with 'orderStatus' as 'PENDING'
    pending_orders = [order for order in response['data'] if order.get('orderStatus') == 'PENDING']

    return pending_orders

def get_traded_order_count_dhan(response):
    # Check if the response contains 'data'
    if 'data' not in response:
        return 0

    # Filter orders with 'orderStatus' as 'TRADED'
    traded_orders = [order for order in response['data'] if order.get('orderStatus') == 'TRADED']

    # Return the count of traded orders
    return len(traded_orders)


import requests
def activate_kill_switch():

    url = "https://api.dhan.co/killSwitch"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "access-token": settings.DHAN_ACCESS_TOKEN
    }
    
    params = {
        "killSwitchStatus": "ACTIVATE"
    }

    response = requests.post(url, headers=headers, params=params)
    print("responseresponseresponse", response)

    if response.status_code == 200:
        response_data = response.json()
        return response_data.get("killSwitchStatus")
    else:
        # Handle error response
        return None



import pandas as pd
from django.http import JsonResponse
from datetime import datetime

def search_csv(formated_der_symbol, formatted_expiry_date):
    print("formated_der_symbol:", formated_der_symbol)
    print("formatted_expiry_date:", formatted_expiry_date)
    file_path = settings.CSV_FILE_PATH
    
    try:
        # Read the CSV file into a pandas DataFrame
        df = pd.read_csv(file_path)

        # Filter the DataFrame based on SEM_TRADING_SYMBOL matching formated_der_symbol
        filtered_df = df[df['SEM_TRADING_SYMBOL'] == formated_der_symbol]

        # Filter further based on SEM_EXPIRY_DATE matching formatted_expiry_date
        filtered_df = filtered_df[filtered_df['SEM_EXPIRY_DATE'] == formatted_expiry_date]

        # Convert the filtered data to a list of dictionaries (JSON serializable format)
        results = filtered_df.to_dict('records')
       
        return results

    except FileNotFoundError:
        return JsonResponse({'error': 'CSV file not found'}, status=404)
    except Exception as e:
        print("Error:", e)
        return JsonResponse({'error': str(e)}, status=500)


    
from datetime import datetime, time
import re
def convert_derivative_symbol(der_symbol, ex_symbol1):
    
    parts = der_symbol.split(':')
    if len(parts) != 2:
        return "Invalid symbol format"
    
    if ex_symbol1 == "NIFTY50":
        ex_symbol1="NIFTY"
    if ex_symbol1 == "NIFTYBANK":
        ex_symbol1="BANKNIFTY"

    details = parts[1]

    # Extract option type
    option_type = details[-2:]

    # Extract strike price (last 5 digits before option type)
    strike_price = details[-7:-2]

    # Remove option type, strike price, and ex_symbol1 from the details
    substrings_to_remove = [option_type, strike_price, ex_symbol1]
    modified_string = details
    print("modified_stringmodified_string",substrings_to_remove )
    for substring in substrings_to_remove:
        modified_string = modified_string.replace(substring, '')

    # What remains is the expiry date
    expiry_date = modified_string
    
    expiry_date = re.sub(r'[a-zA-Z]', '', expiry_date)

    
    print("expiry_dateexpiry_dateexpiry_date", expiry_date)

    # Format expiry date (assuming yyMMdd or yymmdd format)
    if len(expiry_date) == 5:
        year = expiry_date[:2]
        month = expiry_date[2:3]  # Take only one character for month
        day = expiry_date[3:]     # Remaining characters for day
    elif len(expiry_date) == 6:
        year = expiry_date[:2]
        month = expiry_date[2:4]  # Take two characters for month
        day = expiry_date[4:6]    # Two characters for day

    # Map month number to month abbreviation
    months = {
        '1': 'Jan', '2': 'Feb', '3': 'Mar', '4': 'Apr', '5': 'May', '6': 'Jun',
        '7': 'Jul', '8': 'Aug', '9': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec',
    }

    # Get the month abbreviation in title case
    translated_month = months.get(month, '')

    month = month.zfill(2)

    year = "20" + year

    # Construct the translated expiry date in format YYYY-MM-DD HH:MM:SS
    formatted_expiry_date = f"{year}-{month}-{day} 14:30:00"

    # Construct the translated symbol
    translated_symbol = f"{ex_symbol1}-{translated_month}{year}-{strike_price}-{option_type}"

    return translated_symbol, formatted_expiry_date




# STRADDLE WIDGET LIMIT FEATURE 
# 0 - CHECK TIME AND SORT OUT 

# 1 - GET OPTION OTM DATA AND

# 2 - GET HIGHER CLOSET VALUE FOR CALL   

# 3 - GET LOWER CLOSEST VALUE FOR PUT

# 4 - CHECK THEIR LTP Lower than straddle_amount_limit 

# 5 - SET QUANTITY WITH IN THE HALF OF straddle_capital_usage FOR EACH PUT AND CALL 

# 6 - PLACE BUY ORDER 


# ==================================================================================================================================================================

from decimal import Decimal
from django.conf import settings
from django.http import JsonResponse
from .models import TradingConfigurations, OpenOrderTempData
from datetime import datetime, time
import pytz
from django.http import JsonResponse
from decimal import Decimal
import math


def StraddleBuyOrderPlacement(request):
    # try:
    if request.method == 'POST':
        data_instance = get_data_instance(request)
        der_symbol = request.POST.get('der_symbol')
        ex_symbol = request.POST.get('ex_symbol')
        atm_strike =int( request.POST.get('atm_strike'))
        print('atm_strikeatm_strikeatm_strike', atm_strike)
        ltp = Decimal(request.POST.get('ltp'))
        get_lot_count = get_default_lotsize(ex_symbol)
        trade_config_data = TradingConfigurations.objects.order_by('-last_updated').first()
        exchange = "BSE:" if ex_symbol == "SENSEX" else "NSE:"
        data = {"symbol": f"{exchange}{ex_symbol}-INDEX", "strikecount": 1}
        
        # Fetch expiry data
        expiry_response = data_instance.optionchain(data=data)
        if 'error' in expiry_response:  # Check for error response
            return JsonResponse({'response': expiry_response['error']})

        first_expiry_ts = expiry_response['data']['expiryData'][0]['expiry']
        options_data = {"symbol": f"{exchange}{ex_symbol}-INDEX", "strikecount": 4, "timestamp": first_expiry_ts}
        
        # Fetch options data
        response = data_instance.optionchain(data=options_data)
        if 'error' in response:  # Check for error response
            return JsonResponse({'response': response['error']})

        current_strike_price = atm_strike

        # Initialize variables to find closest strike prices
        higher_call_strike = {'strike_price': math.inf, 'data': None}  # Start with infinity for comparison
        lower_put_strike = {'strike_price': -math.inf, 'data': None}   # Start with negative infinity for comparison
        ce_strike = {'strike_price': None, 'data': None}
        pe_strike = {'strike_price': None, 'data': None}

        # Process options chain data to find closest strikes
        options_chain = response['data']['optionsChain']

        # Debug: Print all options data for inspection
        for option in options_chain:
            print(f"itemitemitem {option}")

        for option in options_chain:
            strike_price = option['strike_price']
            
            # # Check for higher closest call strike price
            # if option['option_type'] == 'CE' and strike_price > current_strike_price:
            #     if strike_price < higher_call_strike['strike_price']:
            #         higher_call_strike['strike_price'] = strike_price
            #         higher_call_strike['data'] = option
            
            # # Check for lower closest put strike price
            # if option['option_type'] == 'PE' and strike_price < current_strike_price:
            #     if strike_price > lower_put_strike['strike_price']:
            #         lower_put_strike['strike_price'] = strike_price
            #         lower_put_strike['data'] = option

            # Check for current strike price matches
            if option['option_type'] == 'PE' and strike_price == current_strike_price:
                pe_strike['strike_price'] = strike_price
                pe_strike['data'] = option

            if option['option_type'] == 'CE' and strike_price == current_strike_price:
                ce_strike['strike_price'] = strike_price
                ce_strike['data'] = option

        # Debug: Print found closest and matching strikes
        print(f"Higher Call Strike: {higher_call_strike}")
        print(f"Lower Put Strike: {lower_put_strike}")
        print(f"Current PE Strike: {pe_strike}")
        print(f"Current CE Strike: {ce_strike}")

        # result = [higher_call_strike['data'], lower_put_strike['data'], pe_strike['data'], ce_strike['data']]
        result = [pe_strike['data'], ce_strike['data']]


        ltp_less_than_limit = True
        for item in result:
            print("itemitemitem", item)
            ltp = item['ltp']
            if float(ltp) >= float(trade_config_data.straddle_amount_limit):
                ltp_less_than_limit = False
                break

        if not ltp_less_than_limit:
            message = "Higher LTP value Than Limit."
            return JsonResponse({'response': message})


        trade_config_data = TradingConfigurations.objects.order_by('-last_updated').first()
        allOrderData = data_instance.orderbook()
        total_order_count = sum(1 for order in allOrderData.get("orderBook", []) if order["status"] == 2)
        max_order_count_limit = trade_config_data.max_trade_count
        
        if int(total_order_count) >= int(max_order_count_limit):
            message = "Max Order count limit Reached"
            return JsonResponse({'response': message})
        
        tempDatainstance = OpenOrderTempData.objects.order_by('-last_updated').first()
        if tempDatainstance and tempDatainstance.symbol != der_symbol:
            message = "Unable to place another Symbol Order Now."
            return JsonResponse({'response': message})

        if trade_config_data.order_quantity_mode == "AUTOMATIC":
            print("entry0000000000001")
            limit_amount = trade_config_data.straddle_capital_usage/2
            for strike in result:
                per_lot_expense = strike['ltp'] * get_lot_count
                print("per_lot_expenseper_lot_expenseper_lot_expense", per_lot_expense)
                lotqty = Decimal(limit_amount) // Decimal(per_lot_expense)
                print("lotqtylotqtylotqtylotqty", lotqty)
                order_qty = int(lotqty * get_lot_count)
                if order_qty == 0:
                    message = "Amount Usage Limit Reached"
                    return JsonResponse({'response': message})

                data = {
                    "symbol": strike['symbol'],
                    "qty": order_qty,
                    "type": 2,  # Market Order
                    "side": 1,  # Buy
                    "productType": "MARGIN",
                    "validity": "DAY",
                    "offlineOrder": False
                }

                response = data_instance.place_order(data=data)
                # Assuming data_instance.place_order() returns some response you need to handle
        # Return a success JsonResponse if everything is okay
        return JsonResponse({'response': 'Order placed successfully'})

    else:
        message = "Some Error Occurred Before Execution"
        return JsonResponse({'response': message})



# ==================================================================================================================================================================

def StopLossCalculator(purchase_price: float, loss_percentage: float) -> int:
    stop_loss_price = purchase_price * (1 - loss_percentage / 100)
    return int(round(stop_loss_price))


def trailingwithlimit(request):
    client_id = settings.FYERS_APP_ID
    access_token = request.session.get('access_token')
    
    if access_token:
        fyers = fyersModel.FyersModel(client_id=client_id, token=access_token, log_path="")
        order_data = fyers.orderbook()

        if 'orderBook' not in order_data:
            message = "Error fetching order book data."
            messages.error(request, message)
            return JsonResponse({'message': message})
        
        existing_stop_price = None
        existing_limit_price = None
        symbol = None

        for order in order_data.get("orderBook", []):
            if order.get("status") == 6:
                existing_stop_price = order.get("stopPrice", existing_stop_price)
                existing_limit_price = order.get("limitPrice", existing_limit_price)
                symbol = order.get("symbol", symbol)
        
        if existing_stop_price is not None and existing_limit_price is not None:
            trade_config_data = TradingConfigurations.objects.order_by('-last_updated').first()
            if not trade_config_data:
                message = "No trading configuration data found."
                messages.error(request, message)
                return JsonResponse({'message': message})

            forwrd_trail_limit = Decimal(trade_config_data.forward_trailing_points)

            new_stop_price = Decimal(existing_stop_price) + forwrd_trail_limit
            new_limit_price = Decimal(existing_limit_price) + forwrd_trail_limit

            if symbol:
                data = {"id": order["id"], "type": order["type"], "limitPrice": float(new_limit_price), "stopPrice": float(new_stop_price)}
                trailing_order_update = fyers.modify_order(data=data)

                if 'message' in trailing_order_update:
                    openTempDatainstance = OpenOrderTempData.objects.filter(symbol=symbol).first()
                    if openTempDatainstance:
                        exp_loss = (Decimal(openTempDatainstance.open_traded_price) - new_stop_price) * Decimal(openTempDatainstance.order_qty)
                        openTempDatainstance.sl_price = new_stop_price
                        openTempDatainstance.exp_loss = exp_loss
                        openTempDatainstance.save()
                    
                    message = trailing_order_update['message']
                    messages.success(request, message)
                    return JsonResponse({'message': message})
                else:
                    message = "Error updating trailing order."
                    messages.error(request, message)
                    return JsonResponse({'message': message})
            else:
                message = "No valid orders to modify."
                messages.error(request, message)
                return JsonResponse({'message': message})
        
        message = "No SL/Pending Orders"
        messages.error(request, message)
        return JsonResponse({'message': message})
    
    return redirect('dashboard')

def trailingtodown(request):
    client_id = settings.FYERS_APP_ID
    access_token = request.session.get('access_token')
    
    if access_token:
        fyers = fyersModel.FyersModel(client_id=client_id, token=access_token, log_path="")
        order_data = fyers.orderbook()

        if 'orderBook' not in order_data:
            message = "Error fetching order book data."
            messages.error(request, message)
            return JsonResponse({'message': message})
        
        existing_stop_price = None
        existing_limit_price = None
        symbol = None

        for order in order_data.get("orderBook", []):
            if order.get("status") == 6:
                existing_stop_price = order.get("stopPrice", existing_stop_price)
                existing_limit_price = order.get("limitPrice", existing_limit_price)
                symbol = order.get("symbol", symbol)
        
        if existing_stop_price is not None and existing_limit_price is not None:
            trade_config_data = TradingConfigurations.objects.order_by('-last_updated').first()
            if not trade_config_data:
                message = "No trading configuration data found."
                messages.error(request, message)
                return JsonResponse({'message': message})

            reverse_trail_limit = Decimal(trade_config_data.reverse_trailing_points)

            new_stop_price = Decimal(existing_stop_price) - reverse_trail_limit
            new_limit_price = Decimal(existing_limit_price) - reverse_trail_limit

            if symbol:
                data = {"id": order["id"], "type": order["type"], "limitPrice": float(new_limit_price), "stopPrice": float(new_stop_price)}
                trailing_order_update = fyers.modify_order(data=data)

                if 'message' in trailing_order_update:
                    openTempDatainstance = OpenOrderTempData.objects.filter(symbol=symbol).first()
                    if openTempDatainstance:
                        exp_loss = (Decimal(openTempDatainstance.open_traded_price) - new_stop_price) * Decimal(openTempDatainstance.order_qty)
                        openTempDatainstance.sl_price = new_stop_price
                        openTempDatainstance.exp_loss = exp_loss
                        openTempDatainstance.save()
                    
                    message = trailing_order_update['message']
                    messages.success(request, message)
                    return JsonResponse({'message': message})
                else:
                    message = "Error updating trailing order."
                    messages.error(request, message)
                    return JsonResponse({'message': message})
            else:
                message = "No valid orders to modify."
                messages.error(request, message)
                return JsonResponse({'message': message})
        
        message = "No SL/Pending Orders"
        messages.error(request, message)
        return JsonResponse({'message': message})
    
    return redirect('dashboard')


def trailingtotop(request):
    client_id = settings.FYERS_APP_ID
    access_token = request.session.get('access_token')
    symbol = None

    if access_token:
        fyers = fyersModel.FyersModel(client_id=client_id, token=access_token, log_path="")
        order_data = fyers.orderbook()

        if 'orderBook' not in order_data:
            message = "Error fetching order book data."
            messages.error(request, message)
            return JsonResponse({'message': message})

        for order in order_data.get("orderBook", []):
            if order.get("status") == 6:
                symbol = order.get("symbol", symbol)

        if symbol is not None:
            response = fyers.positions()

            if 'netPositions' not in response:
                message = "Error fetching positions data."
                messages.error(request, message)
                return JsonResponse({'message': message})

            filtered_positions = [position for position in response["netPositions"] if position["symbol"] == symbol]

            if not filtered_positions:
                message = "No matching positions found."
                messages.error(request, message)
                return JsonResponse({'message': message})

            ltp = Decimal(filtered_positions[0]["ltp"])

            trade_config_data = TradingConfigurations.objects.order_by('-last_updated').first()
            if not trade_config_data:
                message = "No trading configuration data found."
                messages.error(request, message)
                return JsonResponse({'message': message})

            trailing_to_top_points = Decimal(trade_config_data.trailing_to_top_points)
            stoploss_limit_slippage = Decimal(trade_config_data.stoploss_limit_slippage)

            new_stop_price = ltp - trailing_to_top_points
            new_limit_price = new_stop_price - stoploss_limit_slippage

            if symbol:
                data = {"id": order["id"], "limitPrice": float(new_limit_price), "stopPrice": float(new_stop_price)}
                trailing_order_update = fyers.modify_order(data=data)

                if 'message' in trailing_order_update:
                    openTempDatainstance = OpenOrderTempData.objects.filter(symbol=symbol).first()
                    if openTempDatainstance:
                        exp_loss = (Decimal(openTempDatainstance.open_traded_price) - new_stop_price) * Decimal(openTempDatainstance.order_qty)
                        openTempDatainstance.sl_price = new_stop_price
                        openTempDatainstance.exp_loss = exp_loss
                        openTempDatainstance.save()

                    message = trailing_order_update['message']
                    messages.success(request, message)
                    return JsonResponse({'message': message})

            else:
                message = "No valid orders to modify."
                messages.error(request, message)
                return JsonResponse({'message': message})

        message = "No SL/Pending Orders"
        messages.error(request, message)
        return JsonResponse({'message': message})

    return redirect('dashboard')




def fyer_websocket_view(request):
    template_name = 'trading_tool/html/fyerwebsocket.html'
    access_token = request.session.get('access_token')
    return render(request, template_name)




from django.http import JsonResponse
def store_current_value_in_session(request):
    if request.method == 'POST':
        #print("qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq")
        # Retrieve data from POST request
        open_symbol = request.POST.get('open_symbol')
        open_qty = request.POST.get('open_qty')
        open_traded_price = request.POST.get('open_traded_price')
        
        # Store data in session
        request.session['open_symbol'] = open_symbol
        request.session['open_qty'] = open_qty
        request.session['open_traded_price'] = open_traded_price
        
        return JsonResponse({'message': 'Current values stored in session successfully.'})
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=400)
    

def get_open_temp_data(request):
    if request.method == 'GET':
        # Retrieve session data
        # open_symbol = request.session.get('open_symbol')
        # open_qty = request.session.get('open_qty')
        # open_traded_price = request.session.get('open_traded_price')
        # exp_stoploss_amount = request.session.get('exp_stoploss_amount')
        openTempDatainstance = OpenOrderTempData.objects.order_by('-last_updated')
        confData = TradingConfigurations.objects.order_by('-last_updated').first()
        print("ENtry111111111111111111111111111111111")
        scalping_mode = confData.scalping_mode
        print("ENtry111111111111111111111111111111111", scalping_mode)
        

        # Check if session data exists
        # if open_symbol is not None and open_qty is not None and open_traded_price is not None:
        if openTempDatainstance.exists():
            print("entry22222222222222222222222222222222222")
            openTempData = openTempDatainstance.first()
            open_symbol = openTempData.symbol
            open_qty = openTempData.quantity
            open_traded_price = openTempData.average_price
            total_order_amount = openTempData.order_total
            exp_loss = openTempData.exp_loss
            exp_stoploss_amount = request.session.get('exp_stoploss_amount')
            sl_price = openTempData.sl_price
            
            print("openTempDataopenTempData", openTempData)
            print("open_symbolopen_symbolopen_symbol", open_symbol)
            print("open_traded_priceopen_traded_price", open_traded_price)
            print("total_order_amounttotal_order_amount", total_order_amount)
            print("exp_stoploss_amountexp_stoploss_amount", exp_stoploss_amount)
            print("sl_pricesl_price", sl_price)
            print("exp_lossexp_loss", exp_loss)
            
            
            return JsonResponse({
                'open_symbol': open_symbol,
                'open_qty': open_qty,
                'open_traded_price': open_traded_price,
                'exp_stoploss_amount': exp_stoploss_amount,
                'total_order_amount': total_order_amount,
                'exp_loss': exp_loss,
                'sl_price': sl_price,
                'scalping_mode': scalping_mode
            })
        else:
            return JsonResponse({'error': 'No Open Position for now'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=400)
    

def remove_session_data(request):
    if request.method == 'POST':
        # Remove session data
        request.session.pop('open_symbol', None)
        request.session.pop('open_qty', None)
        request.session.pop('open_traded_price', None)
        return JsonResponse({'message': 'Session data removed successfully.'})
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=400)
    

def switch_scalp_mode(request):
    if request.method == 'GET':
        # Fetch the latest TradingConfigurations entry
        confData = TradingConfigurations.objects.order_by('-last_updated').first()
        if not confData.scalping_mode:
            capital_limit_per_lot  = confData.scalping_amount_limit
        else:
            capital_limit_per_lot  = confData.capital_limit_per_order
        if confData:
            print("Entry - Toggling scalping_mode")
            # Toggle the scalping_mode value
            confData.scalping_mode = not confData.scalping_mode
            confData.save()
            # Return the updated value as a JsonResponse
            return JsonResponse({'scalping_mode': confData.scalping_mode, 'capital': capital_limit_per_lot })
        else:
            print("No TradingConfigurations entry found.")
            # Return an error if no entry is found
            return JsonResponse({'error': 'No configuration found.'}, status=404)

    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=400)
    

@require_GET
def switch_broker(request):
    # Fetch the latest TradingConfigurations entry
    confData = TradingConfigurations.objects.order_by('-last_updated').first()
    if confData:
        # Toggle the active_broker value
        if confData.active_broker == 'DHAN':
            confData.active_broker = 'FYERS'
        else:
            confData.active_broker = 'DHAN'
        
        # Save the updated configuration
        confData.save()
        
        # Return the updated active_broker value as a JsonResponse
        return JsonResponse({'active_broker': confData.active_broker})
    else:
        print("No TradingConfigurations entry found.")
        # Return an error if no entry is found
        return JsonResponse({'error': 'No configuration found.'}, status=404)


def get_scalp_mode_state(request):
    if request.method == 'GET':
        # Fetch the latest TradingConfigurations entry
        confData = TradingConfigurations.objects.order_by('-last_updated').first()
        if confData.scalping_mode:
            capital_limit_per_lot  = confData.scalping_amount_limit
        else:
            capital_limit_per_lot  = confData.capital_limit_per_order

        
        if confData:
            # Return the updated value as a JsonResponse
            return JsonResponse({'scalping_mode': confData.scalping_mode, 'capital': capital_limit_per_lot })
        else:
            print("No TradingConfigurations entry found.")
            # Return an error if no entry is found
            return JsonResponse({'error': 'No configuration found.'}, status=404)




def get_broker_state(request):
    # Fetch the latest TradingConfigurations entry
    confData = TradingConfigurations.objects.order_by('-last_updated').first()
    if confData:
        # Return the updated value as a JsonResponse
        return JsonResponse({'active_broker': confData.active_broker})
    else:
        print("No TradingConfigurations entry found.")
        # Return an error if no entry is found
        return JsonResponse({'error': 'No configuration found.'}, status=404)