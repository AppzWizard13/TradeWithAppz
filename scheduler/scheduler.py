from account.models import CommonConfig
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fyers_apiv3 import fyersModel
from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
import logging
from django.test import RequestFactory
from fyersapi.models import SOD_EOD_Data, TradingConfigurations, TradingData
from fyersapi.views import calculate_tax, get_data_instance
from django.utils import timezone
logger = logging.getLogger(__name__)
import datetime
from apscheduler.triggers.interval import IntervalTrigger



def automate_sod_task():
    logger.info("Scheduled task is running.")
    try:
        # # Create a fake request object
        # factory = RequestFactory()
        # request = factory.get('/fake-path/')
        # # Apply session middleware
        # middleware = SessionMiddleware()
        # middleware.process_request(request)
        # request.session.save()
        token_data = CommonConfig.objects.filter(param="access_token").get()
        access_token = token_data.value
        client_id = settings.FYERS_APP_ID
        if access_token:
            fyers = fyersModel.FyersModel(
                client_id=client_id, 
                is_async=False, 
                token=access_token,
                log_path=""
            )
            
            # Save positions data
            positions = fyers.positions()
            TradingData.objects.update_or_create(
                category='POSITIONS',last_updated =  timezone.now(),
                defaults={'data': positions, 'last_updated': timezone.now()},
                # other fields
            )
            

            # Save orders data
            orders = fyers.orderbook()
            TradingData.objects.update_or_create(
                category='ORDERS',last_updated =  timezone.now(),
                defaults={'data': orders, 'last_updated': timezone.now()},
                # other fields
            )
            # Save funds data
            funds = fyers.funds()
            TradingData.objects.update_or_create(
                category='FUNDS',last_updated =  timezone.now(),
                defaults={'data': funds, 'last_updated': timezone.now()},
                # other fields
            )
            equity_amount = funds['fund_limit'][0]['equityAmount']
            profit_and_loss_equity = funds['fund_limit'][3]['equityAmount']
            fund_transfer_equity = funds['fund_limit'][5]['equityAmount'] 
            current_date = datetime.date.today()
            # calculate the slippage 
            week_no = current_date.isocalendar()[1]
            # Example values for the model fields
            opening_balance = equity_amount
            closing_balance = 0
            withdrwal_amount = fund_transfer_equity
            deposit_amount = fund_transfer_equity
            day_p_and_l = profit_and_loss_equity
            day_order_count = 0
            day_exp_brokerage = 0
            actual_expense = 0
            actual_benefit = 0
            sod_status = True
            eod_status = False
            trading_date = datetime.date.today()  # Replace with the actual trading date
            sod_data = SOD_EOD_Data.objects.filter(trading_date=trading_date, sod_status=sod_status, week_no=week_no).exists()
            if sod_data  == False :
                # Create a new record
                new_record = SOD_EOD_Data.objects.create(
                    opening_balance=opening_balance,
                    closing_balance=closing_balance,
                    withdrwal_amount=withdrwal_amount,
                    deposit_amount=deposit_amount,
                    day_p_and_l=day_p_and_l,
                    day_order_count=day_order_count,
                    day_exp_brokerage=day_exp_brokerage,
                    actual_expense=actual_expense,
                    actual_benefit=actual_benefit,
                    trading_date=trading_date,
                    week_no = week_no,
                    sod_status = True,
                    eod_status = False
                    # ... other field assignments
                )
            else:
                print("SOD ALREADY COMPLETED FOR THE DAY",trading_date )

            # You can adjust the field values according to your specific use case.
        logger.info(f"Data instance: data_saved")
    except Exception as e:
        logger.error(f"Error running scheduled task: {e}")


def automate_eod_task():
    logger.info("Scheduled task is running.")
    try:
        token_data = CommonConfig.objects.filter(param="access_token").get()
        access_token = token_data.value
        client_id = settings.FYERS_APP_ID

        if access_token:
            fyers = fyersModel.FyersModel(
                client_id=client_id, 
                is_async=False, 
                token=access_token,
                log_path=""
            )
            
            # Save positions data
            positions = fyers.positions()
            TradingData.objects.update_or_create(
                category='POSITIONS',last_updated =  timezone.now(),
                defaults={'data': positions, 'last_updated': timezone.now()},
                # other fields
            )

            # Save orders data
            orders = fyers.orderbook()
            TradingData.objects.update_or_create(
                category='ORDERS',last_updated =  timezone.now(),
                defaults={'data': orders, 'last_updated': timezone.now()},
                # other fields
            )

            # Save funds data
            funds = fyers.funds()
            TradingData.objects.update_or_create(
                category='FUNDS',last_updated =  timezone.now(),
                defaults={'data': funds, 'last_updated': timezone.now()},
                # other fields
            )
            equity_amount = funds['fund_limit'][0]['equityAmount']
            profit_and_loss_equity = funds['fund_limit'][3]['equityAmount']
            fund_transfer_equity = funds['fund_limit'][5]['equityAmount'] 
            current_date = datetime.date.today()
            # calculate the slippage 
            week_no = current_date.isocalendar()[1]
            day_order_count=0
            if "orderBook" in orders:
                day_order_count = sum(1 for order in orders["orderBook"] if order["status"] == 2)

            # closing_balance = 12000
            # day_order_count = 50
            # profit_and_loss_equity = 16000
            closing_balance = equity_amount
            confData = TradingConfigurations.objects.order_by('-last_updated').first()
            cost = confData.capital_limit_per_order
            tax = calculate_tax(cost)
            default_brokerage = settings.DEFAULT_BROKERAGE + tax
            # default_brokerage = settings.DEFAULT_BROKERAGE
            exp_brokerage = default_brokerage * day_order_count
            sod_instance = SOD_EOD_Data.objects.filter(trading_date=current_date, sod_status=True, eod_status=False, week_no=week_no)
            sod_data = sod_instance.first()
            print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            if sod_instance.exists():
                # Update the attributes
                print("***********************************************************************************", sod_data)
                sod_data.closing_balance = closing_balance
                sod_data.withdrwal_amount = fund_transfer_equity
                sod_data.deposit_amount = fund_transfer_equity
                sod_data.day_p_and_l = profit_and_loss_equity
                sod_data.day_order_count = day_order_count
                sod_data.day_exp_brokerage = exp_brokerage
                sod_data.actual_expense = profit_and_loss_equity - exp_brokerage
                sod_data.actual_benefit = float(closing_balance) - float(sod_data.opening_balance)
                sod_data.position_data =  positions,
                sod_data.fund_data =  funds,
                sod_data.order_data =  orders,
                sod_data.eod_status = True

                # Save the updated instance
                sod_data.save()
                print("SOD data updated successfully.")
            else:
                print("No SOD data found for the specified criteria.")

        logger.info(f"Data instance: data_saved")
    except Exception as e:
        logger.error(f"Error running scheduled task: {e}")


def refresh_access_token():
    logger.info("Refreshing access token.")
    try:
        # Get the refresh token from the database
        token_data = CommonConfig.objects.filter(param="refresh_token").get()
        refresh_token = token_data.value
        client_id = settings.FYERS_APP_ID
        secret_key = settings.FYERS_SECRET_ID
        redirect_uri = settings.FYERS_REDIRECT_URL + "/dashboard"

        # Create a session object to handle the Fyers API authentication and token refresh
        session = fyersModel.SessionModel(
            client_id=client_id,
            secret_key=secret_key,
            redirect_uri=redirect_uri,
            response_type="code",
            grant_type="refresh_token"
        )
        session.set_token(refresh_token)
        response = session.refresh_token()
        access_token = response.get('access_token')
        new_refresh_token = response.get('refresh_token')

        if access_token and new_refresh_token:
            # Remove existing tokens from the database
            CommonConfig.objects.filter(param__in=['access_token', 'refresh_token']).delete()
            
            # Insert new tokens into the database
            CommonConfig.objects.create(
                param='access_token',
                value=access_token
            )
            CommonConfig.objects.create(
                param='refresh_token',
                value=new_refresh_token
            )
            logger.info("Access token refreshed successfully.")
        else:
            logger.error("Failed to refresh access token. Missing access_token or refresh_token.")
    except Exception as e:
        logger.error(f"Error refreshing access token: {e}")


def resetovertradestatus():
    logger.info("Scheduled task is running.")
    try:
        TradingConfigurations.objects.order_by('-last_updated').update(over_trade_status=False)
        # # Create a fake request object
    except Exception as e:
        logger.error(f"Error running scheduled task: {e}")


def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(automate_sod_task, CronTrigger(hour=9, minute=15))
    # scheduler.add_job(automate_eod_task, IntervalTrigger(seconds=10))
    scheduler.add_job(automate_eod_task, CronTrigger(hour=15, minute=00))
    scheduler.add_job(resetovertradestatus, CronTrigger(hour=8, minute=35))
    # scheduler.add_job(refresh_access_token, IntervalTrigger(minutes=15)) 
    # scheduler.add_job(automate_eod_task,CronTrigger(day_of_week='mon-fri',hour='9-15', minute=30))
    # scheduler.add_job(automate_eod_task, IntervalTrigger(seconds=10))
    scheduler.start()
    logger.info("Scheduler started.")

    # Shut down the scheduler when exiting the app
    import atexit
    atexit.register(lambda: scheduler.shutdown())
