import json
from channels.generic.websocket import AsyncWebsocketConsumer,WebsocketConsumer
from fyers_apiv3.FyersWebsocket.data_ws import FyersDataSocket
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from fyers_apiv3.FyersWebsocket import order_ws
from django.conf import settings
from fyers_apiv3 import fyersModel
from fyers_apiv3.FyersWebsocket import data_ws
import hashlib
import requests
import hashlib
import requests
from channels.generic.websocket import WebsocketConsumer
from fyers_apiv3.FyersWebsocket import order_ws
from django.conf import settings
from account.models import CommonConfig
from fyersapi.views import get_data_instance
import time

class FyersPositionDataConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        # Generate app_id_hash
        self.app_id = settings.FYERS_APP_ID
        secret_key = settings.FYERS_SECRET_ID
        app_id_hash = self.generate_app_id_hash(self.app_id, secret_key)
        pin = "2772"
        session = self.scope["session"]
        refresh_token = session.get("refresh_token")

        url = "https://api-t1.fyers.in/api/v3/validate-refresh-token"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "grant_type": "refresh_token",
            "appIdHash": app_id_hash,
            "refresh_token": refresh_token,
            "pin": pin
        }

        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            json_response = response.json()
            access_token = json_response.get("access_token")
            access_token = self.app_id + ":" + access_token

            self.fyers = order_ws.FyersOrderSocket(
                access_token=access_token, 
                write_to_file=False,
                log_path="",
                on_connect=self.onopen,
                on_close=self.onclose,
                on_error=self.onerror,
                on_positions=self.onPosition,
            )
            self.fyers.connect()
        else:
            self.send(text_data=f"Error: {response.text}")

    def disconnect(self, close_code):
        self.close()

    def onopen(self):
        data_type = "OnPositions"
        self.fyers.subscribe(data_type=data_type)
        self.fyers.keep_running()

    def onPosition(self, message):
        self.send(text_data=f"Position Response: {message}")

    def onerror(self, message):
        self.send(text_data=f"Error: {message}")

    def onclose(self, message):
        self.send(text_data=f"Connection closed: {message}")

    @staticmethod
    def generate_app_id_hash(client_id, secret_key):
        concatenated_string = f"{client_id}:{secret_key}"
        hash_object = hashlib.sha256(concatenated_string.encode())
        return hash_object.hexdigest()

class FyersIndexDataConsumer(WebsocketConsumer):
    print('entry______________________________________1')
    def connect(self):
        self.accept()

        self.last_keyword = self.scope['url_route']['kwargs']['last_keyword']  
        if self.last_keyword == "SENSEX":
            exchnage =  "BSE:"
        else:
            exchnage =  "NSE:"
            
        self.symbols = [exchnage + self.last_keyword + "-INDEX"]
        self.app_id = settings.FYERS_APP_ID
        secret_key = settings.FYERS_SECRET_ID
        app_id_hash = self.generate_app_id_hash(self.app_id, secret_key)
        pin = "2772"
        session = self.scope["session"]
        refresh_data = CommonConfig.objects.filter(param="refresh_token").first()
        refresh_token = refresh_data.value
        
        print('refresh_tokenrefresh_tokenrefresh_tokenrefresh_token', refresh_token)


        url = "https://api-t1.fyers.in/api/v3/validate-refresh-token"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "grant_type": "refresh_token",
            "appIdHash": app_id_hash,
            "refresh_token": refresh_token,
            "pin": pin
        }

        response = requests.post(url, headers=headers, json=data)
        print('responseresponseresponseresponse', response)
        if response.status_code == 200:
            json_response = response.json()
            self.access_token = json_response.get("access_token")
            self.getoptionsymbols, self.optioncancelsymbols = self.getOptionStrikes()

            self.fyers = data_ws.FyersDataSocket(
                access_token=self.access_token,
                log_path="",
                litemode=True,
                write_to_file=False,
                reconnect=True,
                on_connect=self.on_open,
                on_close=self.on_close,
                on_error=self.on_error,
                on_message=self.on_message
            )

            self.fyers.connect()
        else:
            self.send(text_data=f"Error: {response.text}")

    def disconnect(self, close_code):
        data_type = "SymbolUpdate"
        self.closing_symbols = self.optioncancelsymbols + self.symbols
        print('---------------------------------------------------')
        print('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx', self.closing_symbols)
        print('---------------------------------------------------')
        self.fyers.unsubscribe(symbols=self.closing_symbols, data_type=data_type)
        self.close()

    def on_open(self):
        data_type = "SymbolUpdate"
        self.allsymbols = self.symbols + self.getoptionsymbols
        self.fyers.subscribe(symbols=self.allsymbols, data_type=data_type)
        self.fyers.keep_running()

    def on_message(self, message):
        try:
            # Parse the message if it's a string, assuming the message might already be a dict
            if isinstance(message, str):
                data = json.loads(message)
            else:
                data = message  # If it's already a dict, use it directly

            # Ensure the message has 'symbol' and 'ltp'
            if 'symbol' in data and 'ltp' in data:
                symbol = data['symbol']

                # Define the checking key based on your symbol setup
                # checking_key = self.symbols[0].split('-')[0]  # Extracts 'NSE:MIDCPNIFTY' from 'NSE:MIDCPNIFTY-INDEX'

                # Check if 'checking_key' is part of the symbol
                if self.checking_key in symbol:
                    # Prepare the formatted message
                    formatted_message = {
                        'symbol': symbol,
                        'ltp': data['ltp'],
                        'type': data.get('type', 'unknown')  # Fallback if 'type' is not present
                    }

                    # Send the message to the WebSocket client as a JSON string
                    self.send(text_data=json.dumps(formatted_message))
                else:
                    if self.checking_key == "NSE:BANKNIFTY":
                        if symbol == "NSE:NIFTYBANK-INDEX":
                            formatted_message = {
                            'symbol': symbol,
                            'ltp': data['ltp'],
                            'type': data.get('type', 'unknown')  # Fallback if 'type' is not present
                            }
                            self.send(text_data=json.dumps(formatted_message))
                    # If symbol doesn't match the checking key, ignore the message
                    print(f"Ignoring message with unmatched symbol: {symbol}")
            else:
                print("Message does not contain 'symbol' or 'ltp':", data)

        except json.JSONDecodeError as e:
            # Handle JSON decoding errors
            print("Error decoding message JSON:", str(e))
            self.send(text_data="Error decoding message")

        except Exception as e:
            # General exception handling
            print("Error processing message:", str(e))
            self.send(text_data="Error processing message")



    def on_error(self, message):
        self.send(text_data=f"Error: {message}")

    def on_close(self, message):
        data_type = "SymbolUpdate"
        print('-----------------------------------------')
        print('oooooooooooooooooooooooo', self.allsymbols)
        print('-----------------------------------------')
        self.fyers.unsubscribe(symbols=self.allsymbols, data_type=data_type)
        self.close()
        self.send(text_data=f"Connection closed: {message}")

    @staticmethod
    def generate_app_id_hash(client_id, secret_key):
        concatenated_string = f"{client_id}:{secret_key}"
        hash_object = hashlib.sha256(concatenated_string.encode())
        return hash_object.hexdigest()
        
    def getOptionStrikes(self):
        self.fyers = fyersModel.FyersModel(client_id=self.app_id, is_async=False, token=self.access_token, log_path="")
        
        data = {
            "symbol": self.symbols[0],
            "strikecount": 1,
        }
        
        try:
            self.expiry_response = self.fyers.optionchain(data=data)
            first_expiry_ts = self.expiry_response['data']['expiryData'][0]['expiry']
            
            if first_expiry_ts:
                # Extract the 'checking_key' by slicing 'NSE:MIDCPNIFTY' from 'self.symbols[0]'
                self.checking_key = self.symbols[0].split('-')[0]
                print('self.checking_key', self.checking_key)
                if self.checking_key == "NSE:NIFTYBANK":
                    self.checking_key = "NSE:BANKNIFTY"
                elif self.checking_key == "NSE:NIFTY50":
                    self.checking_key = "NSE:NIFTY"
                
                # Original 4-strike logic for symbol_list
                options_data = {
                    "symbol": self.symbols[0],
                    "strikecount": 4, 
                    "timestamp": first_expiry_ts
                }
                print('self.symbols[0]:', self.symbols[0])
                
                response = self.fyers.optionchain(data=options_data)
                options_chain = response['data']['optionsChain']
                
                # Filter and sort PE options that contain 'checking_key' in their symbol
                pe_options_sorted = sorted(
                    [option for option in options_chain if option['option_type'] == 'PE'],
                    key=lambda x: x['strike_price'],
                    reverse=True
                )
                
                # Filter and sort CE options
                ce_options_sorted = sorted(
                    [option for option in options_chain if option['option_type'] == 'CE'],
                    key=lambda x: x['strike_price']
                )
                print('pe_options_sorted', pe_options_sorted)

                # Symbols for original 4 strikes
                self.pe_symbols = [option['symbol'] for option in pe_options_sorted]
                self.ce_symbols = [option['symbol'] for option in ce_options_sorted]
                
                symbol_list = self.ce_symbols + self.pe_symbols

                # API call for 30 strikes to populate symbols_close_list
                close_data = {
                    "symbol": self.symbols[0],
                    "strikecount": 30,  # Separate API call for 30 strikes
                    "timestamp": first_expiry_ts
                }

                close_response = self.fyers.optionchain(data=close_data)
                close_options_chain = close_response['data']['optionsChain']

                # Filter and sort PE and CE options for close list
                pe_close_sorted = sorted(
                    [option for option in close_options_chain if option['option_type'] == 'PE'],
                    key=lambda x: x['strike_price'],
                    reverse=True
                )
                ce_close_sorted = sorted(
                    [option for option in close_options_chain if option['option_type'] == 'CE'],
                    key=lambda x: x['strike_price']
                )
                
                # Symbols for the 30 strikes
                pe_symbols_close = [option['symbol'] for option in pe_close_sorted]
                ce_symbols_close = [option['symbol'] for option in ce_close_sorted]

                symbols_close_list = ce_symbols_close + pe_symbols_close
                
                return symbol_list, symbols_close_list

        except (KeyError, AttributeError, IndexError, Exception) as e:
            error_message = f'Error occurred: {str(e)}'
            print("Error occurred while fetching option data:", error_message)
            
        return [], []  # Return empty lists if there's an error


    def receive(self, text_data):
        message = json.loads(text_data)
        action = message.get('action')

        if action == 'disconnect':
            data_type = "SymbolUpdate"
            self.fyers.unsubscribe(symbols=self.allsymbols, data_type=data_type)
            self.close()