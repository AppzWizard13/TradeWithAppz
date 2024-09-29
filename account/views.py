from django.conf import settings
from django.shortcuts import redirect, render
from account.forms import UserLoginForm, UserprofileUpdate
from django.contrib import auth
from django.views import View  
from django.contrib.auth import logout
from django.contrib import messages
from account.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.views.generic.list import ListView
from datetime import datetime
from django.db.models import Sum
from django.urls import reverse_lazy
from django.views.generic import CreateView
from fyersapi.models import TradingConfigurations, TradingData
from fyersapi.views import brokerconnect, calculate_tax, get_accese_token_store_session, get_data_instance, get_traded_order_count_dhan
from scheduler.scheduler import automate_sod_task, automate_eod_task 
from .forms import CustomUserCreationForm
from django.contrib.auth import authenticate, login
from decimal import Decimal
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.contrib import messages
from urllib.parse import urlparse, parse_qs
from django.contrib.auth.decorators import login_required
import time
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from urllib.parse import urlparse, parse_qs
from django.contrib import messages
import time
from django.contrib.auth.mixins import LoginRequiredMixin
from dhanhq import dhanhq
from account.models import CommonConfig



def homePage(request):
    return render(request,'accounts/index.html')

class DashboardView(LoginRequiredMixin, TemplateView):
    login_url = '/login'
    template_name = "trading_tool/html/index.html"
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        try:
            current_url = request.build_absolute_uri()
            parsed_url = urlparse(current_url)
            query_params = parse_qs(parsed_url.query)
            auth_code = query_params.get('auth_code', [''])[0]
            if auth_code:
                request.session['auth_code'] = auth_code
                messages.success(request, 'Auth code stored successfully.')
            else:
                messages.error(request, 'Failed to extract auth code from the URL.')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}. No broker connected.')

        # Delay the execution of get_access_token function by 1 second
        time.sleep(1)
        get_accese_token_store_session(request)
        automate_sod_task()
        access_token = request.session.get('access_token')
        data_instance = get_data_instance(request)
        dhan_client_id = settings.DHAN_CLIENTID
        dhan_access_token = settings.DHAN_ACCESS_TOKEN
        try:
            self.positions_data = data_instance.positions()
        except AttributeError as e:
            self.positions_data = {'code': -1, 'message': f'Error occurred: {str(e)}', 's': 'error'}
            #print("Error occurred while fetching positions data:", e)

        try:
            self.order_data = data_instance.orderbook()
        except AttributeError as e:
            self.order_data = {'code': -1, 'message': f'Error occurred: {str(e)}', 's': 'error'}
            #print("Error occurred while fetching order data:", e)

        try:
            self.fund_data = data_instance.funds()
        except AttributeError as e:
            self.fund_data = {'code': -1, 'message': f'Error occurred: {str(e)}', 's': 'error'}
            #print("Error occurred while fetching fund data:", e)
            
        # try:
        #     dhan = dhanhq(dhan_client_id, dhan_access_token)
        #     self.dhan_fund = dhan.get_fund_limits()
        #     self.orderlist = dhan.get_order_list()
            
        # except AttributeError as e:
        #     self.fund_data = {'code': -1, 'message': f'Error occurred: {str(e)}', 's': 'error'}
            

        self.total_order_status = 0
        self.pending_orders_status_6 = 0
        confData = TradingConfigurations.objects.order_by('-last_updated').first()
        cost = confData.capital_limit_per_order
        self.active_broker = confData.active_broker
        print("active_brokeractive_broker", self.active_broker)
        self.expected_brokerage = 0 
        tax = calculate_tax(cost)
        default_brokerage = settings.DEFAULT_BROKERAGE + tax
        self.recent_order_data = []
        trading_config = TradingConfigurations.objects.order_by('-last_updated').first()
        # #print("self.order_limitself.order_limit", self.order_limit) 
        #  trading_config.max_trade_count
        self.order_limit =  trading_config.max_trade_count
        self.progress_percentage= 0
        if self.active_broker == "FYERS":
            if self.order_data and "orderBook" in self.order_data:
                # Filter orders with status 6
                filled_orders = [order for order in self.order_data["orderBook"] if order["status"] == 2]
                # Sort pending orders by orderDateTime in descending order
                filled_orders_sorted = sorted(filled_orders, key=lambda x: x["orderDateTime"], reverse=True)
                # Iterate over the first 10 items in the sorted data
                for order in filled_orders_sorted[:10]:
                    self.recent_order_data.append(order)
                # Update pending order count
                self.pending_orders_status_6 = sum(1 for order in self.order_data["orderBook"] if order["status"] == 6)
                # Update total order count for status 2
                self.total_order_status = sum(1 for order in self.order_data["orderBook"] if order["status"] == 2)
                
        if self.active_broker == "DHAN ":
                self.total_order_status = get_traded_order_count_dhan(self.orderlist)
            

        self.remaining_orders = self.order_limit - self.total_order_status
        self.progress_percentage = (self.remaining_orders / self.order_limit) * 100
        self.progress_percentage = round(self.progress_percentage, 1)
        self.expected_brokerage = self.total_order_status * default_brokerage
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order_limit'] = self.order_limit
        context['order_data'] = self.order_data
        context['fund_data'] = self.fund_data
        context['total_order_status'] = self.total_order_status
        context['progress_percentage'] = self.progress_percentage
        context['pending_orders_status'] = self.pending_orders_status_6
        context['expected_brokerage'] = self.expected_brokerage
        context['recent_order_data'] = self.recent_order_data
        context['positions_data'] = self.positions_data
        # context['dhan_fund'] = self.dhan_fund['data']['availabelBalance']
        context['active_broker'] = self.active_broker

        return context

class UserloginView(View):
    def get(self, request):
        template = "trading_tool/html/authentication-login.html"
        context = {}
        context['form'] = UserLoginForm()
        #print("context", context)
        logged_user = request.user

        if logged_user.is_authenticated:
            #print(logged_user)
            #print("dashboard__form")
            return redirect('brokerconnect')  
        else:
            #print(logged_user)
            #print("login__form")
            return render(request, template, context)
        
    def logoutUser(self, request):  # Make sure to include `self` as the first parameter for methods in a class
        #print("logout_processing")
        logout(request)
        automate_eod_task()
        messages.success(request, "Logout Successful !")
        return redirect('login')

    def post(self, request):
        context={}
        form = UserLoginForm(request.POST)
        context['form']= form
        template = "trading_tool/html/authentication-login.html"
        if request.method == "POST":
            if form.is_valid():
                login_username = request.POST["username"]
                login_password = request.POST["password"]
                #print(login_username)
                #print(login_password)
                user = auth.authenticate(username=login_username, password=login_password)
                if user :
                # if user is not None and  user.is_superuser==False and user.is_active==True:
                    auth.login(request, user)
                    #print("login success")
                    messages.success(request, "Login Successful !")
                    # return render(request, "user/dashboard.html")
                    return redirect('brokerconnect')  
                else:
                    #print("user not Exists")
                    # messages.info(request, "user not Exists")
                    messages.error(request, 'Username or Password incorrect !')
                    return render(request, template, context)
            else:
                #print("user not created")
                return render(request, template, context)
            

class UserRegistrationView(CreateView):
    form_class = CustomUserCreationForm
    template_name = "trading_tool/html/authentication-register.html"
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)

        # Authenticate and log in the user
        username = form.cleaned_data['username']
        password = form.cleaned_data['password1']
        messages.success(self.request, 'Registration completed successfully')
        user = authenticate(username=username, password=password)
        messages.success(self.request, 'redirected to Dashboard')
        login(self.request, user)
        return response

class MemberListView(View):
    def get(self, request , **kwargs):
        template = "user/accountmanage.html"
        breadcrumb = {"1":"Member Management", "2":"Manage member" }
        label = { 'title' : "Manage member" }
        header = { "one": 'First Name',"two" : 'Last Name', "three" : "User Name",}
        Data =  User.objects.all()
        context = {'header':header , 'label':label, "breadcrumb":breadcrumb ,"Data": Data}
        return render(request, template, context)

class SuccessView(View):
    def get(self, request):
        template = "success_page.html"
        context={}
        #print("context", context)
        return render(request, template, context)


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.conf import settings
from datetime import datetime
import json

@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')

            print("passwordpassword", password)
            print('usernameusername', username)
            
            user = authenticate(request, username=username, password=password)

            
            if user is not None:
                auth_code_url = brokerconnect(request, app=True)
                # Authentication successful
                client_id = settings.FYERS_APP_ID
                secret_key = settings.FYERS_SECRET_ID
                access_data = CommonConfig.objects.filter(param="access_token").first()
                refresh_data = CommonConfig.objects.filter(param="refresh_token").first()
                # Check if the access_token exists
                if access_data is None or not access_data.value and refresh_data is None or not refresh_data.value:
                    # Return JSON response with the specific message
                    return JsonResponse({
                        "message": "Please login in web with Fyers then retry with the mobile app."
                    }, status=402)  # HTTP 402 Payment Required status code
                
                access_token = access_data.value
                refresh_token = refresh_data.value
                print("access_tokenaccess_tokenaccess_token")
                
                # Get current date and time
                now = datetime.now()
                timestamp = now.strftime('%Y-%m-%d %H:%M:%S')  # Format timestamp
                date = now.date().isoformat()  # Format date

                return JsonResponse({
                    'message': 'Login successful',
                    'access_token': refresh_token,
                    'refresh_token': refresh_token,
                    'client_id': client_id,
                    'secret_key': secret_key,
                    'timestamp': timestamp,
                    'date': date,
                    'auth_code_url': auth_code_url
                }, status=200)
            else:
                # Authentication failed
                return JsonResponse({'error': 'Invalid username or password'}, status=401)
        
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    return JsonResponse({'error': 'Invalid HTTP method'}, status=405)

from django.http import JsonResponse
from django.contrib.auth import logout
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth import logout

@csrf_exempt
def api_logout(request):
    if request.method == 'POST':
        logout(request)
        return JsonResponse({'message': 'Successfully logged out.'}, status=200)
    return JsonResponse({'error': 'Invalid request method.'}, status=400)

    
        
from django.middleware.csrf import get_token
from django.http import JsonResponse

@csrf_exempt
def csrf_token_view(request):
    csrf_token = get_token(request)
    print("csrf_tokencsrf_tokencsrf_token", csrf_token)
    return JsonResponse({'csrf_token': csrf_token}, status=200)

from django.http import JsonResponse
from fyersapi.models import TradingConfigurations

def fetch_trade_configurations(request):
    try:
        # Fetch the latest TradingConfigurations instance
        latest_config = TradingConfigurations.objects.latest('last_updated')
        
        # Serialize the data
        data = {
            'default_stoploss': str(latest_config.default_stoploss),
            'default_order_qty': latest_config.default_order_qty,
            'reward_ratio': latest_config.reward_ratio,
            'max_loss': latest_config.max_loss,
            'max_trade_count': latest_config.max_trade_count,
            'capital_limit_per_order': latest_config.capital_limit_per_order,
            'capital_usage_limit': latest_config.capital_usage_limit,
            'forward_trailing_points': latest_config.forward_trailing_points,
            'trailing_to_top_points': latest_config.trailing_to_top_points,
            'reverse_trailing_points': latest_config.reverse_trailing_points,
            'stoploss_limit_slippage': str(latest_config.stoploss_limit_slippage),
            'last_updated': latest_config.last_updated.isoformat(),
            'averaging_limit': latest_config.averaging_limit,
            'order_quantity_mode': latest_config.order_quantity_mode,
            'scalping_amount_limit': latest_config.scalping_amount_limit,
            'scalping_mode': latest_config.scalping_mode,
            'scalping_stoploss': str(latest_config.scalping_stoploss),
            'scalping_ratio': latest_config.scalping_ratio,
            'straddle_amount_limit': latest_config.straddle_amount_limit,
            'straddle_capital_usage': latest_config.straddle_capital_usage,
            'over_trade_status': latest_config.over_trade_status,
            'averaging_qty': latest_config.averaging_qty,
            'active_broker': latest_config.active_broker,
        }
        
        return JsonResponse(data, status=200)
    
    except TradingConfigurations.DoesNotExist:
        return JsonResponse({'error': 'No trading configurations found.'}, status=404)


# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from django.views.decorators.http import require_POST
# import docker
# import json

# client = docker.from_env()

# @csrf_exempt
# @require_POST
# def restart_container(request):
#     try:
#         data = json.loads(request.body)
#         container_id = data.get('container_id')
#         if not container_id:
#             return JsonResponse({'error': 'Container ID required'}, status=400)

#         container = client.containers.get(container_id)
#         container.restart()
#         return JsonResponse({'status': 'Container restarted successfully'}, status=200)

#     except docker.errors.NotFound:
#         return JsonResponse({'error': 'Container not found'}, status=404)
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500)
@csrf_exempt
def sell_webhook(request):
    if request.method == 'POST':
        try:
            payload = json.loads(request.body)
            # Process the payload here
            print('incoming_socket_data')
            print(payload)
            return JsonResponse({'status': 'success'}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'invalid JSON'}, status=400)
    else:
        return JsonResponse({'status': 'invalid method'}, status=405)