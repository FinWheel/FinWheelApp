import requests
from dotenv import *
from bank.models import *
from user.models import *
from hashlib import sha256
import datetime 
from json import JSONEncoder
from bank.plaid_tools import *
import decimal

auth = dotenv_values("bank/.env")
print(auth)
"""
def create_new_customer(User, phone, address_list, ssn, dob, ip_address):
    url = "https://sandbox.bond.tech/api/v0/customers/"
    kyc_user = KYC(address=address_list["street"], state=address_list["state"], zipCode=address_list["zip_code"], city=address_list["city"], ssn=sha256(f'{ssn}'.encode("utf-8")).hexdigest(), dob=dob, ip_address=ip_address, phone=phone)
    payload = {
        "dob": dob,
        "first_name": User.first_name,
        "last_name": User.last_name,
        "ssn": ssn,
        "phone": phone,
        "phone_country_code": "1",
        "email": User.email,
        "addresses": [
            address_list
        ]
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Identity": auth["id"],
        "Authorization": auth["auth"]
    }

    response = requests.post(url, json=payload, headers=headers)
    kyc_user.save()
    
    print(response.json())
    kyc_user.customer_id = response.json()["customer_id"]
    kyc_user.save()
    kj = CashAccount.objects.get(for_user=User)
    kj.customer_id = response.json()["customer_id"]
    kj.save()
    start_KYC(KYC, ssn)
"""

def alpaca_account_making(User: User, phone, address_list, ssn, dob, ip_address):
    import requests
    date_time = f"2024-07-15T21:18:31Z"
    url = "https://broker-api.sandbox.alpaca.markets/v1/accounts"
    kyc_user = KYC(address=address_list["street"], state=address_list["state"], zipCode=address_list["zip_code"], city=address_list["city"], ssn=sha256(f'{ssn}'.encode("utf-8")).hexdigest(), dob=dob, ip_address=ip_address, phone=phone)
    payload = {
        "contact": {
            "email_address": User.email,
            "phone_number": phone,
            "city": address_list["city"],
            "state": address_list["state"],
            "postal_code": address_list["zip_code"],
            "street_address": address_list["street"],
            "unit": address_list["unit"]
        },
        "identity": {
            "tax_id_type": "USA_SSN",
            "given_name": User.first_name,
            "family_name": User.last_name,
            "date_of_birth": dob,
            "tax_id": ssn,
            # extra stuff we need to ask lol
            "country_of_citizenship": "USA",
            "country_of_tax_residence": "USA",
            "country_of_birth": "USA",
            "funding_source": ["employment_income"]
        },
        "disclosures": {
            "is_control_person": False,
            "is_affiliated_exchange_or_finra": False,
            "is_politically_exposed": False,
            "immediate_family_exposed": False,
            "employment_status": "employed"
        },
        "trusted_contact": {
            "given_name": User.first_name,
            "family_name": User.last_name,
            "email_address": User.email,
            "street_address": [address_list["street"]],
            "city": address_list["city"],
            "state": address_list["state"],
            "postal_code": address_list["zip_code"],
            "country": "USA",
            "phone_number": phone,
        },
        "agreements": [
            { "agreement": "margin_agreement", 
            "signed_at": date_time, "ip_address": ip_address,
            },
            { "agreement": "account_agreement", "signed_at":  date_time, "ip_address": ip_address,},
            { "agreement": "customer_agreement", "signed_at": date_time, "ip_address": ip_address, },
            
        ],
        "documents": [
            {
                "document_type": "identity_verification",
                "content": "/9j/Cg==",
                "mime_type": "image/jpeg"
            }
        ],
        "enabled_assets": ["us_equity"]
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": "Basic Q0tCTVA1M0taSVc1V0JST0pUQlg6MnpsWGJncWJ3VU9xbGxFajVoeWJONnRvTGFpOE1rZVBjcUgyS09KOQ=="
    }

    response = requests.post(url, json=payload, headers=headers)

    print(response.text)
    print(response.status_code)
    bank_account = ExternalBankAccount.objects.get(for_user=User)
    if response.status_code == 200:
        kyc_user.customer_id = response.json()["id"]
        kyc_user.save()
        try:
            kj = CashAccount.objects.get(for_user=User)
            bank_account = kj.bank_account
            kj.customer_id = response.json()["id"]
        except CashAccount.DoesNotExist:
            bank_account = ExternalBankAccount.objects.get(for_user=User)
            kj = CashAccount(for_user=User, cash_balance=0.00, customer_id=response.json()["id"], bank_account=bank_account)
        kj.save()
        xt = validateBank(response.json()["id"], bank_account)
        if xt.status_code == 200:
            return response.status_code
        else:
            return xt.json()["message"]
    else:
        bank_account.delete()
        return response.json()["message"]
    
def validateBank(alpaca_account_id, bank_info: ExternalBankAccount):
    import requests

    url = f"https://broker-api.sandbox.alpaca.markets/v1/accounts/{alpaca_account_id}/recipient_banks"

    payload = {
        "bank_code_type": "ABA",
        "name": bank_info.bank_name,
        "bank_code": bank_info.bank_routing_number,
        "account_number": bank_info.bank_account_number
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": "Basic Q0tCTVA1M0taSVc1V0JST0pUQlg6MnpsWGJncWJ3VU9xbGxFajVoeWJONnRvTGFpOE1rZVBjcUgyS09KOQ=="
    }

    response = requests.post(url, json=payload, headers=headers)

    print(response.text)
    return response

def check_if_account_is_verified(alpaca_account_id, external_bank_account):
    import requests

    url = f"https://broker-api.sandbox.alpaca.markets/v1/accounts/{alpaca_account_id}/recipient_banks"

    headers = {"accept": "application/json", "authorization": "Basic Q0tCTVA1M0taSVc1V0JST0pUQlg6MnpsWGJncWJ3VU9xbGxFajVoeWJONnRvTGFpOE1rZVBjcUgyS09KOQ=="}

    response = requests.get(url, headers=headers)

    accounts = list(response.text)
    if response.json()[0]["status"] != "APPROVED":
        print(response.json()[0]["status"])
        return False
    else:
        external_bank_account.verified = True
        external_bank_account.save()
        return True

def create_ACH_relationship(account_id, bank_account: ExternalBankAccount):
    import requests

    url = f"https://broker-api.sandbox.alpaca.markets/v1/accounts/{account_id}/ach_relationships"

    payload = {
        "bank_account_type": "CHECKING",
        "bank_account_number": bank_account.bank_account_number,
        "bank_routing_number": bank_account.bank_routing_number,
        "account_owner_name": f"{bank_account.for_user.first_name} {bank_account.for_user.last_name}",
        "instant": True,
        #"processor_token": processor_token
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": "Basic Q0tCTVA1M0taSVc1V0JST0pUQlg6MnpsWGJncWJ3VU9xbGxFajVoeWJONnRvTGFpOE1rZVBjcUgyS09KOQ=="
    }

    response = requests.post(url, json=payload, headers=headers)

    print(response.text)
    if response.status_code == 409 or response.status_code == 200:
        k = check_on_ACH_relationship(account_id)
        if k == False:
            return False
        else:
            return True
    elif response.status_code == 400:
        return False
        
def get_open_orders(acct: CashAccount):
    import requests

    url = f"https://broker-api.sandbox.alpaca.markets/v1/trading/accounts/{acct.customer_id}/orders?status=open"

    headers = {"accept": "application/json", "authorization": "Basic Q0tCTVA1M0taSVc1V0JST0pUQlg6MnpsWGJncWJ3VU9xbGxFajVoeWJONnRvTGFpOE1rZVBjcUgyS09KOQ=="}

    response = requests.get(url, headers=headers)

    print(response.text)
    return response.json()

def check_on_ACH_relationship(account_id):
    import requests

    url = f"https://broker-api.sandbox.alpaca.markets/v1/accounts/{account_id}/ach_relationships"

    headers = {"accept": "application/json", "authorization": "Basic Q0tCTVA1M0taSVc1V0JST0pUQlg6MnpsWGJncWJ3VU9xbGxFajVoeWJONnRvTGFpOE1rZVBjcUgyS09KOQ=="}

    response = requests.get(url, headers=headers)

    #print(response.text)
    #print(response.json())
    if response.json()[0]["status"] != "APPROVED":
        return False
    else:
        return True


def pull_ach_relationships(account_id):
    import requests

    url = f"https://broker-api.sandbox.alpaca.markets/v1/accounts/{account_id}/ach_relationships"

    headers = {"accept": "application/json", "authorization": "Basic Q0tCTVA1M0taSVc1V0JST0pUQlg6MnpsWGJncWJ3VU9xbGxFajVoeWJONnRvTGFpOE1rZVBjcUgyS09KOQ=="}

    response = requests.get(url, headers=headers)

    return response.json()[0]["id"]



def make_transaction(account: CashAccount, alpaca_info, acc_num, amount, order):
    import requests
    print(type(amount))
    url = f"https://broker-api.sandbox.alpaca.markets/v1/accounts/{account.customer_id}/transfers"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": "Basic Q0tCTVA1M0taSVc1V0JST0pUQlg6MnpsWGJncWJ3VU9xbGxFajVoeWJONnRvTGFpOE1rZVBjcUgyS09KOQ=="
    }
    payload = None
    record = Transaction(amount=amount, date_executed=datetime.datetime.now(), for_account=account)
    if order == "INCOMING": # deposit
        payload = {
            "transfer_type": "ach",
            "direction": "INCOMING",
            "timing": "immediate",
            "relationship_id": pull_ach_relationships(account.customer_id),
            "amount": amount,
            "fee_payment_method": "user"
        }
        record.transaction_type = "DEP"
        #account.cash_balance += decimal.Decimal(amount)
    elif order == "OUTGOING":
        record.transaction_type = "WTH"
        if decimal.Decimal(alpaca_info["cash_withdrawable"]) >= decimal.Decimal(amount):
            payload = {
                "transfer_type": "ach",
                "direction": "OUTGOING",
                "timing": "immediate",
                "relationship_id": pull_ach_relationships(account.customer_id),
                "amount": amount,
                "fee_payment_method": "user"
            }
            #account.cash_balance -= decimal.Decimal(amount)
        else:
            return "Withdrawal request amount over the amount of cash withdrawable"
        
    
    response = requests.post(url, json=payload, headers=headers)

    print(response.text)
    print(response.status_code)
    if response.status_code != 200:
        return response.json()["message"]
    else:
        account.save()
        record.save()
        eba = ExternalBankAccount.objects.get(for_user=account.for_user)
        try:
            import os
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            message = Mail(
                from_email='customer-service@finwheel.tech',
                to_emails=account.for_user.email,
                subject='Transaction Made',
                html_content=f"""
                    <!DOCTYPE html>
                    <html lang="en">

                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>Money Transfer Confirmation</title>
                    </head>

                    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0;">
                        <div style="max-width: 600px; margin: 20px auto; background-color: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);">
                            <div style="text-align: center; margin-bottom: 20px;">
                                <img src="https://media.licdn.com/dms/image/D560BAQFYbp34o5N4Cg/company-logo_200_200/0/1713541491138?e=2147483647&v=beta&t=899Yiqf5482L3zz8Rq2cZ4Bxzx6QL2j1OBClsBCSfcc" alt="FinWheel Logo" style="max-width: 150px;">
                            </div>
                            <h1 style="color: #333333; text-align: center;">Money Transfer Confirmation</h1>
                            <p style="color: #666666; line-height: 1.6;">Dear {account.for_user.first_name},</p>
                            <p style="color: #666666; line-height: 1.6;">We are pleased to inform you that your recent money transfer between your bank account and your FinWheel account was successful.</p>
                            
                            <div style="margin: 20px 0;">
                                <p style="margin: 5px 0; color: #666666;"><strong style="color: #333333;">Transfer Amount:</strong> ${amount}</p>
                                <p style="margin: 5px 0; color: #666666;"><strong style="color: #333333;">Date:</strong> {datetime.datetime.now()}</p>
                                <p style="margin: 5px 0; color: #666666;"><strong style="color: #333333;">Transaction Type:</strong> {payload["direction"]}</p>
                                <p style="margin: 5px 0; color: #666666;"><strong style="color: #333333;">From/To Account:</strong> {eba.bank_name} - {eba.bank_account_number}</p>
                            </div>

                            <p style="color: #666666; line-height: 1.6;">If you have any questions or concerns, please feel free to contact our support team at customer-service@finwheel.tech</p>
                            <p style="color: #666666; line-height: 1.6;">Thank you for trusting FinWheel with your investment management needs!</p>
                            
                            <a href="https://finwheel.tech/bank/investments" style="display: inline-block; background-color: #007BFF; color: #ffffff; padding: 10px 20px; border-radius: 5px; text-decoration: none; text-align: center; margin-top: 20px;">View Your Account</a>

                            <div style="text-align: center; color: #999999; font-size: 12px; margin-top: 20px;">
                                <p>&copy; 2024 FinWheel. All rights reserved.</p>
                                <p>FinWheel Inc., 123 Financial Road, Suite 456, Financial City, FS 78901</p>
                            </div>
                        </div>
                    </body>

                    </html>


                """)
            sg = SendGridAPIClient(auth['SENDGRID_API_KEY'])
            response = sg.send(message)
        except Exception as e:
            print(e)
            print("email failed")
        return True


def get_news(asset):
    import requests

    url = f"https://data.alpaca.markets/v1beta1/news?sort=desc&symbols={asset}&include_content=true"

    headers = {"accept": "application/json","APCA-API-KEY-ID": "PKGFLKPMUCPMK13R0UQW","APCA-API-SECRET-KEY": "rWg3Ho4fnC3niaEuejw1nLgaOezN7Ve0c3ZzBMUf"}

    response = requests.get(url, headers=headers)

    print(response.text)
    return response.json()


def get_positions_from_account(user: CashAccount):
    import requests

    url = f"https://broker-api.sandbox.alpaca.markets/v1/trading/accounts/{user.customer_id}/positions"

    headers = {"accept": "application/json","authorization": "Basic Q0tCTVA1M0taSVc1V0JST0pUQlg6MnpsWGJncWJ3VU9xbGxFajVoeWJONnRvTGFpOE1rZVBjcUgyS09KOQ=="}

    response = requests.get(url, headers=headers)

    #print(response.text)
    print(response.json())
    return list(response.json())

def cancel_order(user:CashAccount, order_id):
    import requests

    url = f"https://broker-api.sandbox.alpaca.markets/v1/trading/accounts/{user.customer_id}/orders/{order_id}"

    headers = {"accept": "application/json", "authorization": "Basic Q0tCTVA1M0taSVc1V0JST0pUQlg6MnpsWGJncWJ3VU9xbGxFajVoeWJONnRvTGFpOE1rZVBjcUgyS09KOQ=="}

    response = requests.delete(url, headers=headers)

    print(response.text)



def get_account_info(acct: CashAccount):
    import requests

    url = f"https://broker-api.sandbox.alpaca.markets/v1/trading/accounts/{acct.customer_id}/account"

    headers = {"accept": "application/json", "authorization": "Basic Q0tCTVA1M0taSVc1V0JST0pUQlg6MnpsWGJncWJ3VU9xbGxFajVoeWJONnRvTGFpOE1rZVBjcUgyS09KOQ=="}

    response = requests.get(url, headers=headers)

    print(response.text)
    return response.json()

def get_quote(symbol):
    import requests

    url = f"https://data.alpaca.markets/v2/stocks/{symbol}/quotes/latest?feed=iex"

    headers = {"accept": "application/json", "APCA-API-KEY-ID": "PKGFLKPMUCPMK13R0UQW","APCA-API-SECRET-KEY": "rWg3Ho4fnC3niaEuejw1nLgaOezN7Ve0c3ZzBMUf"}

    response = requests.get(url, headers=headers)

    print(response.text)

    return response.json()

def process_order(ticker, side, type, time, qty, cash_amt, pricept: float, cash_account: CashAccount):
    import requests
    try:
        ticker = str(ticker)
        side = str(side)
        type = str(type)
        if qty != None:
            qty = float(qty)
        if cash_amt != None:
            cash_amt = float(cash_amt)
        if pricept != None:
            pricept = int(pricept)
    except Exception as e:
        print(e)
        return False
    acct_info = dict(get_account_info(cash_account))
    print(acct_info)
    positions = get_positions_from_account(cash_account)
    quote = get_quote(ticker)["quote"]["ap"]
    buying_power = None
    cash = None
    position_qty = None
    position_exists = None
    if str(side).lower() == "buy":
        buying_power = acct_info["buying_power"]
        cash = float(acct_info["cash"])
        if qty != None:
            if (quote*qty) > cash:
                return "Order Not Executed: Not Enough Cash"
            else:
                cash_account.cash_balance -= decimal.Decimal((quote*float(qty)))
        else:
            if cash_amt > cash:
                return "Order Not Executed: Not Enough Cash"
            else:
                cash_account.cash_balance -= decimal.Decimal(float(cash_amt))
    else:
        for x in positions:
            if x["symbol"] == ticker:
                position_exists = True
                position_qty = x["qty"]
                break
        if position_exists == False or float(qty) > float(position_qty):
            return "You are selling more stock than you actually have."
        else:
            cash_account.cash_balance += decimal.Decimal((quote*float(qty)))
    

    url = f"https://broker-api.sandbox.alpaca.markets/v1/trading/accounts/{cash_account.customer_id}/orders"

    payload = {
        "side": side,
        "type": str(type).lower(),
        "time_in_force": time,
        "commission_type": "notional",
        "symbol": ticker,
        "qty": qty,    
    }

    if type == "limit" or type == "stop_limit":
        payload.update({"limit_price": pricept})
    if type == "stop" or type == "stop_limit":
        payload.update({"stop_price": pricept})
    if type == "trailing_stop":
        payload.update({"trail_price": pricept})

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": "Basic Q0tCTVA1M0taSVc1V0JST0pUQlg6MnpsWGJncWJ3VU9xbGxFajVoeWJONnRvTGFpOE1rZVBjcUgyS09KOQ=="
    }

    response = requests.post(url, json=payload, headers=headers)
    cash_account.save()
    if response.status_code != 200:
        return response.json()["message"]
    else: 
        print(response.text)
        try:
            import os
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            message = Mail(
                from_email='customer-service@finwheel.tech',
                to_emails=cash_account.for_user.email,
                subject='Order Submitted',
                html_content=f"""
                        <!DOCTYPE html>
                        <html lang="en">

                        <head>
                            <meta charset="UTF-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            <title>Stock Order Confirmation</title>
                        </head>

                        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0;">
                            <div style="max-width: 600px; margin: 20px auto; background-color: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);">
                                <div style="text-align: center; margin-bottom: 20px;">
                                    <img src="https://media.licdn.com/dms/image/D560BAQFYbp34o5N4Cg/company-logo_200_200/0/1713541491138?e=2147483647&v=beta&t=899Yiqf5482L3zz8Rq2cZ4Bxzx6QL2j1OBClsBCSfcc" alt="FinWheel Logo" style="max-width: 150px;">
                                </div>
                                <h1 style="color: #333333; text-align: center;">Stock Order Confirmation</h1>
                                <p style="color: #666666; line-height: 1.6;">Dear {cash_account.for_user.first_name},</p>
                                <p style="color: #666666; line-height: 1.6;">Your recent stock order has been successfully placed. Below are the details of your order:</p>
                                
                                <div style="margin: 20px 0;">
                                    <p style="margin: 5px 0; color: #666666;"><strong style="color: #333333;">Order ID:</strong> {response.json()["id"]}</p>
                                    <p style="margin: 5px 0; color: #666666;"><strong style="color: #333333;">Stock Name:</strong> {ticker}</p>
                                    <p style="margin: 5px 0; color: #666666;"><strong style="color: #333333;">Order Type:</strong> {side}</p>
                                    <p style="margin: 5px 0; color: #666666;"><strong style="color: #333333;">Quantity:</strong> {qty}</p>
                                    <p style="margin: 5px 0; color: #666666;"><strong style="color: #333333;">Price per Share:</strong> ${pricept if pricept != None else get_quote(ticker)['quote']['ap']}</p>
                                    <p style="margin: 5px 0; color: #666666;"><strong style="color: #333333;">Total Amount:</strong> ${round(quote*qty,ndigits=2)}</p>
                                    <p style="margin: 5px 0; color: #666666;"><strong style="color: #333333;">Order Date:</strong> {datetime.datetime.now()}</p>
                                </div>

                                <p style="color: #666666; line-height: 1.6;">You can view the status of your order and your portfolio in your FinWheel account.</p>
                                
                                <a href="https://your-website.com" style="display: inline-block; background-color: #007BFF; color: #ffffff; padding: 10px 20px; border-radius: 5px; text-decoration: none; text-align: center; margin-top: 20px;">View Your Portfolio</a>

                                <div style="text-align: center; color: #999999; font-size: 12px; margin-top: 20px;">
                                    <p>&copy; 2024 FinWheel. All rights reserved.</p>
                                    <p>FinWheel Inc., 123 Financial Road, Suite 456, Financial City, FS 78901</p>
                                </div>
                            </div>
                        </body>

                        </html>

                """)
            sg = SendGridAPIClient(auth['SENDGRID_API_KEY'])
            res = sg.send(message)
        except Exception as e:
            print(e)
            print("email failed")
        return response.json()["id"]



def load_documents_and_transactions(acct: CashAccount, type: str):

    url = f"https://broker-api.sandbox.alpaca.markets/v1/accounts/{acct.customer_id}/documents?type={type}"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": "Basic Q0tCTVA1M0taSVc1V0JST0pUQlg6MnpsWGJncWJ3VU9xbGxFajVoeWJONnRvTGFpOE1rZVBjcUgyS09KOQ=="
    }
    response = requests.get(url, headers=headers)

    return response.json()

def find_document(account: CashAccount, doc_id):
    import requests

    url = f"https://broker-api.sandbox.alpaca.markets/v1/accounts/{account.customer_id}/documents/{doc_id}/download"

    headers = {"authorization": "Basic Q0tCTVA1M0taSVc1V0JST0pUQlg6MnpsWGJncWJ3VU9xbGxFajVoeWJONnRvTGFpOE1rZVBjcUgyS09KOQ=="}

    response = requests.get(url, headers=headers)
    #print(response.is_redirect)
    print(response.text)
    response_dict = vars(response.history[0])
    for var_name, var_value in response_dict.items():
        print(f"{var_name}: {var_value}")
    f = open('res.pdf', 'ab')
    f.write(str(response.text).encode("utf_8"))
    f.close()
    print(dict(response.history[0].headers)['Location'])
    return dict(response.history[0].headers)['Location']

def get_alpaca_transfers(account: CashAccount):
    import requests

    url = f"https://broker-api.sandbox.alpaca.markets/v1/accounts/{account.customer_id}/transfers"
    print(url)
    headers = {
        "accept": "application/json",
        "authorization": "Basic Q0tCTVA1M0taSVc1V0JST0pUQlg6MnpsWGJncWJ3VU9xbGxFajVoeWJONnRvTGFpOE1rZVBjcUgyS09KOQ=="
    }

    response = requests.get(url, headers=headers)
    #print(response.text)
    return response.json()

def get_user_portfolio_history(account: CashAccount, period, timeframe):
    import requests

    url = f"https://broker-api.sandbox.alpaca.markets/v1/trading/accounts/{account.customer_id}/account/portfolio/history?period={period}&timeframe={timeframe}&intraday_reporting=market_hours&pnl_reset=per_day"

    headers = {"accept": "application/json", "authorization": "Basic Q0tCTVA1M0taSVc1V0JST0pUQlg6MnpsWGJncWJ3VU9xbGxFajVoeWJONnRvTGFpOE1rZVBjcUgyS09KOQ=="}

    response = requests.get(url, headers=headers)

    return response.json()