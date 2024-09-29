from . import views
from django.urls import path
from django.contrib.auth import views as auth_views
from fyersapi.views import Brokerconfig
from .views import ConfigureTradingView



urlpatterns = [
    path('broker_config', views.Brokerconfig.as_view(), name='broker_config'),
    path('brokerconnect', views.brokerconnect, name='brokerconnect'),
    path('get_accese_token_store_session', views.get_accese_token_store_session, name='get_accese_token_store_session'),
    path('get_user_profile', views.ProfileView.as_view(), name='get_user_profile'),





    path('trading-calender-view', views.TradingCalenderView.as_view(), name='trading_calender_view'),
    path('sod-config-process', views.SOD_Config_Process, name='sod_config_process'),
    path('eod-reporting-view', views.EOD_ReportingView.as_view(), name='eod_reporting_view'),
    path('fetch-date-data/', views.fetch_date_data, name='fetch_date_data'),
    path('daily-candle-overview/', views.daily_candle_overview, name='daily_candle_overview'),


    
    path('candle-overview/', views.CandleOverviewView.as_view(), name='candle_overview'),



    path('close_all_positions', views.close_all_positions, name='close_all_positions'),
    # path('api/close_all_positions/', views.api_close_all_positions, name='api_close_all_positions'),
    path('api/close_all_positions/', views.close_all_positions, name='api_close_all_positions'),
    
    
    
    path('update-data-instance/', views.update_data_instance, name='update_data_instance'),
    path('partial_exit_positions', views.partial_exit_positions, name='partial_exit_positions'),
 

    # order history
    path('order-history/', views.OrderHistory.as_view(), name='order_history'),
    path('transaction_history/', views.TransactionHistory.as_view(), name='transaction_history'),
    




    path('update-latest-data', views.update_latest_data, name='update_latest_data'),
    # path('get-options-data', views.get_options_data, name='get_options_data'),
    # path('options-chain-view', views.OptionChainView.as_view(), name='options_chain_view'),
    path('options-chain-view/<str:slug>/', views.OptionChainView.as_view(), name='options_chain_view'),
    path('configure-trading/', ConfigureTradingView.as_view(), name='configure_trading'),
    path('instant-buy-order/', views.instantBuyOrderWithSL, name='instant_buy_order'),
   

    path('straddle-buy-order/', views.StraddleBuyOrderPlacement, name='straddle_buy_order'),



    

    # Trailing Orders
    path('trailingwithlimit/', views.trailingwithlimit, name='trailingwithlimit'),
    path('trailingtodown/', views.trailingtodown, name='trailingtodown'),
    path('trailingtotop/', views.trailingtotop, name='trailingtotop'),


    path('store_current_value_in_session/', views.store_current_value_in_session, name='store_current_value_in_session'),
    path('get_open_temp_data/', views.get_open_temp_data, name='get_open_temp_data'),
    path('get_scalp_mode_state/', views.get_scalp_mode_state, name='get_scalp_mode_state'),
    path('switch_scalp_mode/', views.switch_scalp_mode, name='switch_scalp_mode'),
    path('remove_session_data/', views.remove_session_data, name='remove_session_data'),

    path('get_broker_state/', views.get_broker_state, name='get_broker_state'),
    path('switch_broker/', views.switch_broker, name='switch_broker'),


    


    




    

    





    path('explore-more/', views.fyer_websocket_view, name='explore_more'),




    
    

    
    # path('logout', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

   


      

]
