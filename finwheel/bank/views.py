from django.shortcuts import render, HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, login, authenticate
from requests import HTTPError
from user.models import *
from django.urls import reverse
from bank.models import *
from bank.utils import *
from bank.banking_tools import *
import json
import plaid
from dotenv import dotenv_values
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.country_code import CountryCode
from plaid.model.link_token_transactions import LinkTokenTransactions
from plaid.model.link_token_account_filters import LinkTokenAccountFilters
from plaid.model.credit_filter import CreditFilter
from plaid.model.depository_filter import DepositoryFilter
from plaid.model.depository_account_subtypes import DepositoryAccountSubtypes
from plaid.model.depository_account_subtype import DepositoryAccountSubtype
from plaid.model.credit_account_subtypes import CreditAccountSubtypes
from plaid.model.credit_account_subtype import CreditAccountSubtype
from plaid import api_client
from plaid.model.products import Products
#from tests.integration.util import create_client
from django.shortcuts import redirect
from plaid.model.link_token_create_request_auth import LinkTokenCreateRequestAuth
from django.http import JsonResponse

stuff = dotenv_values('bank/.env')
client_id = stuff['CLIENT_ID']
secret = stuff['SECRET']
#client = create_client(client_id, secret)

# Create your views here.

@login_required(login_url='/user/login')
def index(request):
    config_bank = False
    #print(get_user_portfolio_history(CashAccount.objects.get(for_user=request.user)))
    if request.method == "GET":
        if CashAccount.objects.filter(for_user=request.user).count() < 1 or ExternalBankAccount.objects.filter(for_user=request.user).count() < 1:
            config_bank = True
        if config_bank:
            return render(request, "bank/index.html", {
                "config_bank": config_bank
            })
        else:
            user_account = CashAccount.objects.get(for_user=request.user)
            xt = check_if_account_is_verified(user_account.customer_id,ExternalBankAccount.objects.get(for_user=request.user))
            print(xt)
            if xt and user_account.bank_account.ach_authorized != True:
                #return HttpResponseRedirect(reverse("bank:achverification"))
                x = create_ACH_relationship(user_account.customer_id, user_account.bank_account)
                if x:
                    user_account.bank_account.ach_authorized = True
                    user_account.bank_account.save()
                else:
                    config_bank = True
                return render(request, "bank/index.html", {
                    "user_account": user_account,
                    "config_bank": config_bank
                })
            else:
                return render(request, "bank/index.html", {
                    "user_account": user_account,
                    "account_info": get_account_info(acct=user_account),
                    "config_bank": config_bank,
                    "transactions": list(get_alpaca_transfers(CashAccount.objects.get(for_user=request.user)))
                })

@login_required(login_url='/user/login')
def take_portfolio_data(request):
    if request.method == "POST":
        data = json.loads(request.body)
        period = data["timePeriod"]
        timeframe = "1D"
        if "5D" in period:
            timeframe = "1D"
        elif "1D" in period:
            timeframe = "1H"
        elif "A" in period:
            timeframe = "1D"
        elif "M" in period:
            timeframe = "1D"
        new_stuff = get_user_portfolio_history(CashAccount.objects.get(for_user=request.user), period=period, timeframe=timeframe)
        return JsonResponse(new_stuff)


#keep for a moment -> modify to making it take SSN with the other info to create a new bank acct. 
@login_required(login_url='/user/login')
def set_up_bank(request):
    config_bank = False
    ip = request.META.get('REMOTE_ADDR')
    if request.method == "POST":
        if CashAccount.objects.filter(for_user=request.user).count() < 1 or ExternalBankAccount.objects.filter(for_user=request.user).count() < 1:
            config_bank = True
            # add area for taking an address info. 
        if config_bank:
            address = {
                "address_type": "MAILING",
                "is_primary": True,
                "street": request.POST["street"],
                "city": request.POST["city"],
                "state": request.POST["state"],
                "zip_code": request.POST["zip"],
                "unit": request.POST["unit"],
                "country": "USA"
            }
            try:
                bank = ExternalBankAccount.objects.get(for_user=request.user)
            except ExternalBankAccount.DoesNotExist:
                bank = ExternalBankAccount(for_user=request.user, bank_name=request.POST["name"], bank_account_number=request.POST["AccNum"], bank_routing_number=request.POST["RoutNum"], verified=False)
                bank.save()
            verify = alpaca_account_making(request.user, request.POST["number"], address, request.POST["ssn"], request.POST["dob"], ip)
            if verify == 200:
                """
                config_bank = False
                user_account = CashAccount.objects.get(for_user=request.user)
                return render(request, "bank/index.html", {
                    "user_account": user_account,
                    "config_bank": config_bank
                })
                """
                return HttpResponseRedirect(reverse("bank:dashboard"))
            else:
                return render(request, "bank/index.html", {
                    "message": verify,
                    "config_bank": config_bank
                })
        else:
            user_account = CashAccount.objects.get(for_user=request.user)
            return render(request, "bank/index.html", {
                "user_account": user_account,
                "config_bank": config_bank
            })
        # take the customer ID and store it within the user profile
        #begin the process of KYC Verification. 

@login_required(login_url='/user/login')
def account_view(request):
    pass

@login_required(login_url='/user/login')
def card_view(request):
    pass

@login_required(login_url='/user/login')
def investment_view(request):
    user_account = CashAccount.objects.get(for_user=request.user)
    positions = get_positions_from_account(user_account)
    print(positions)
    account_info = get_account_info(acct=user_account)
    print(account_info)
    orders = get_open_orders(user_account)
    return render(request, "bank/investments.html", {"positions": positions, "orders":orders, "acct":account_info, "cash": account_info["cash"]})     

@login_required(login_url='/user/login')
def cancel_order_view(request, order_id):
    user_account = CashAccount.objects.get(for_user=request.user)
    cancel_order(user_account, order_id)
    return HttpResponseRedirect(reverse("bank:investments"))

@login_required(login_url='/user/login')
def transactions_view(request):
    all_documents = load_documents_and_transactions(acct=CashAccount.objects.get(for_user=request.user), type="")
    all_statements = load_documents_and_transactions(acct=CashAccount.objects.get(for_user=request.user), type="account_statement")
    tax_documents = load_documents_and_transactions(acct=CashAccount.objects.get(for_user=request.user), type="tax_statement")
    trade_confirmations = load_documents_and_transactions(acct=CashAccount.objects.get(for_user=request.user), type="trade_confirmation")
    print(trade_confirmations)
    return render(request, "bank/account_stats.html", {
        "tax_doc_count": len(tax_documents),
        "tax_documents": tax_documents,
        "trade_confirmations": trade_confirmations,
        "trade_confirmations_count": len(trade_confirmations),
        "all_statements": all_statements,
        "all_statements_count": len(all_statements),
        "account_id": CashAccount.objects.get(for_user=request.user).customer_id
    })

@login_required(login_url='/user/login')
def view_document(request, doc_id):
    if request.method == "GET":
        xt = find_document(CashAccount.objects.get(for_user=request.user), doc_id)
        return render(request, "bank/pdf.html", {"u": xt})


#transaction management
@login_required(login_url="/user/login")
def start_transaction(request):
    l = ExternalBankAccount.objects.filter(for_user=request.user, verified=True, ach_authorized=True)
    if request.method == "GET":
        cash_account = CashAccount.objects.get(for_user=request.user)
        alpaca_acct = get_account_info(acct=cash_account)
        return render(request, "bank/transaction.html", {"external_bank_accounts": l, "cash": alpaca_acct})
    else:
        bank = request.POST["bank"]
        amount = request.POST["amount"]
        order_type = request.POST["order_type"]
        cash_account = CashAccount.objects.get(for_user=request.user)
        alpaca_acct = get_account_info(acct=cash_account)
        lk = make_transaction(cash_account, alpaca_acct, bank, amount, order_type)
        if lk != True:
            print(lk)
            return render(request, "bank/transaction.html", {"external_bank_accounts": l, "cash": alpaca_acct, "message": lk})
        else:
            return HttpResponseRedirect(reverse("bank:dashboard"))

@login_required(login_url="/user/login")
def make_order(request):
    cash_account = CashAccount.objects.filter(for_user=request.user)
    l = ExternalBankAccount.objects.filter(for_user=request.user, verified=True, ach_authorized=True)
    if request.method == "GET":
        alpaca_acct = []
        for n in cash_account:
            alpaca_acct.append(get_account_info(n))
        return render(request, "bank/order.html", {"external_bank_accounts": l, "accts": alpaca_acct})
    else:
        ticker = request.POST["stock_tick"]
        side = request.POST["order_side"]
        type = request.POST["order_type"]
        qty = request.POST["amount"]
        time = request.POST["order_time"]
        acct = request.POST["account_number"]
        pricept = 0
        if "price" in request.POST.keys():  
            pricept = float(request.POST["price"])
        choice = request.POST["choice"]
        cash_account = CashAccount.objects.get(for_user=request.user, customer_id=acct)
        if choice == "dollars":
            xt = process_order(ticker, side, type, time, qty=None,cash_amt=qty, pricept=pricept, cash_account=cash_account)
        elif choice == "shares":
            xt = process_order(ticker, side, type, time, qty=qty, cash_amt=None, pricept=pricept, cash_account=cash_account)
        try:
            import uuid
            uu = uuid.UUID(xt)
        except Exception:
            return render(request, "bank/order.html", {"external_bank_accounts": l, "cash": cash_account, "message": xt})
        else:
            print("order processed")
            print(xt)
            return HttpResponseRedirect(reverse("bank:investments"))
       
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET", "POST"])
def hook_receiver_view(request): # KYC ONLY
    # Listens only for GET and POST requests
    # returns django.http.HttpResponseNotAllowed for other requests

    # Handle the event appropriately
    return HttpResponse('success')


@login_required(login_url="/user/login")
def latest_quote(request):
    if request.method == "POST":
        symbol = json.loads(request.body)
        print(symbol)
        xt = get_quote(symbol["symbol"])
        print(xt)
        #return JsonResponse({"price": xt["quote"]["ap"]})
        return HttpResponse(f'{dict(xt)["quote"]["bp"]}')
    


"""
@login_required(login_url='/user/login')
def send_to_plaid(request):
    if request.method == 'GET':
        # Account filtering isn't required here, but sometimes 
        # it's helpful to see an example. 
        requestz = LinkTokenCreateRequest(
        user=LinkTokenCreateRequestUser(
            client_user_id='user-id',
            phone_number='+1 415 555 0123'
        ),
        client_name='FinWheel Investments',
        products=[Products('auth')],
        country_codes=[CountryCode('US')],
        language='en',
        required_if_supported_products=[Products('identity')],
        #webhook='https://sample-web-hook.com',
        #redirect_uri='https://127.0.0.1:8000/bank',
        auth=LinkTokenCreateRequestAuth(
            automated_microdeposits_enabled=True
        )
        )
        response = client.link_token_create(requestz)
        link_token = response['link_token']
        print(link_token)
        #return render(request, "bank/plaid.html", {"token": str(link_token)})
        return redirect(f"https://cdn.plaid.com/link/v2/stable/link.html?isWebview=true&token={link_token}")
    else:
        data = json.loads(request.body)
        x = CashAccount.objects.get(for_user=request.user)
        p_token = get_plaid_processor_token(account_id=x.customer_id, public_token=data["public_token"])
        k = create_ACH_relationship(account_id=x.customer_id, bank_account=x.bank_account, processor_token=p_token)
        return HttpResponseRedirect(reverse("bank:dashboard"))
        """