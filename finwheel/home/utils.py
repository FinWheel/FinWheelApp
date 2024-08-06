from home.views import *
from bank.models import *
from user.models import *
def verify_setup(user):
    verification_list = []
    # verify the user set up everything

    # 1. Check to see if they verified their bank/info
    account = CashAccount.objects.get(for_user=user)
    if account.bank_account.verified == True:
        verification_list.append(True)
    else:
        verification_list.append(False)
    # 2. Create a financial plan with Fin
    try:
        financePlan = FinancialPlan.objects.get(for_user=user)
        verification_list.append(True)
    except Exception:
        verification_list.append(False)
    
    return verification_list
