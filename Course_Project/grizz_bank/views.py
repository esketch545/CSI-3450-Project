import random
import hashlib
from django.core.mail import *
from django.conf import settings

from django.shortcuts import render, redirect
from .models import *  # import all of the model classes
from django.http import HttpResponse, HttpResponseRedirect
from django.db import transaction, IntegrityError
from django.contrib import messages

import re  # regular expressions
import decimal
import datetime
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import pytz
utc=pytz.UTC

SESSION_EXPIRATION = 60  # login cookie time to live in minutes
ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
# Create your views here.


def index(request):
    """
    def create_account_data_list(accounts):
        # dictionary mapping account type key to an actual account type name
        types = {"S": "Savings", "C": "Checking"}
        # List comprehension returning a list of dicitonaries containing account type, balance, and ID
        acct_data = [{"type": types[acct.acct_type], "bal": acct.acct_bal, "id": acct.acct_id} for acct in accounts]
        return acct_data
    """
    if "sessionid" not in request.COOKIES or (request.session.get_expiry_age() == 0):
        print("Session not set, or expired")
        return HttpResponseRedirect(f"/grizz_bank/login/?status_message=expired_session")
    uname = request.session.get("uname", None)
    if request.session.get("uname", None) is None:
        print("uname is None :)")
        return HttpResponseRedirect(f"/grizz_bank/login/?status_message=invalid_session")

    # TODO: Add login cookie check/refresh here, on failure redirect to login page
    print(f"Cookies: {request.COOKIES}")
    context = {}
    uname =  request.session.get("uname", None)
    print(request.session.get_expiry_age())
    try:
        client_id = Client.objects.get(username=uname).client_id
        client_accounts = Account.objects.filter(client_id=client_id)
        # List comprehension to build a list of python dictionaries containing account data into the context
        context["account_data"] = create_account_data_list(client_accounts)
        context["error"] = False
    except Exception as e:
        # If an error happens log to console, set context error flag true, and make account data an empty list
        print(e)
        context["error"] = True
        context["account_data"] = list()

    
    return render(request, "grizz_bank/index.html", context)

    #this view renders the create_account template,
    #redirects the page to the index or home page,
    # and should send a message request to display a
    # Success! message if account creation is successful
def create_account(request):
    """
    Django view responsible for rendering the create account web page.
    :param request: django HTTP get request
    :return: Django response with rendered HTML
    """
    context = {}
    #call create_client view
    #create_client(request)
    #return redirect('index')
    return render(request, "grizz_bank/create_account.html", context)

def reset_password(request):
    """
    Django view which renders the reset password web page
    :param request: django HTTP get request
    :return: Django response with rendered HTML
    """
    if "sessionid" not in request.COOKIES or (request.session.get_expiry_age() == 0):
        print("Session not set, or expired")
        return HttpResponseRedirect(f"/grizz_bank/login/?status_message=expired_session")
    if request.session.get("uname", None) is None:
        print("uname is None :)")
        return HttpResponseRedirect(f"/grizz_bank/login/?status_message=invalid_session")
    context ={}
    return render(request, "grizz_bank/reset_password.html", context)

def forgot_password(request):
    context = {}
    return render(request, "grizz_bank/forgot_password.html", context)

def login(request):
    """
    login page view which renders the GrizzBank login page.
    :param request:
    :return:
    """
    '''
    print("cookies:", request.COOKIES)
    print(request.COOKIES.get('expiration'))
    print(date)
    print(date < request.COOKIES.get('expiration'))
    '''
    date = str(datetime.datetime.now())
    if "expiration" in request.COOKIES and date < request.COOKIES.get('expiration'):
        return HttpResponseRedirect(f"/grizz_bank?uname={request.COOKIES.get('uname')}&status=Login_success")
    else:
        context ={}
        return render(request, "grizz_bank/login.html", context)


def transfer(request):
    """
    Django view handling business logic to render a web page where users transfer money between their checkings and
    savings accounts.
    :param request: Django HTTPS GET Request
    :return: HTTPS Response with HTML rendered per transfer.html template
    """
    # Redirect to login if client not logged in
    if "sessionid" not in request.COOKIES or (request.session.get_expiry_age() == 0):
        print("Session not set, or expired")
        return HttpResponseRedirect(f"/grizz_bank/login/?status_message=expired_session")
    uname = request.session.get("uname", None)
    if request.session.get("uname", None) is None:
        print("uname is None :)")
        return HttpResponseRedirect(f"/grizz_bank/login/?status_message=invalid_session")
    context = fetch_acct_data(uname)
    return render(request, "grizz_bank/transfer.html", context)


def deposit(request):
    """
    Django view to handle business logic needed to render the deposit page a client uses to deposit money into one of
    their checking or savings accounts.
    :param request: HTTP django request object
    :return: Django HTTPResponse with rendered deposit page HTML
    """
    # Redirect to login if client not logged in or session expired
    if "sessionid" not in request.COOKIES or (request.session.get_expiry_age() == 0):
        print("Session not set, or expired")
        return HttpResponseRedirect(f"/grizz_bank/login/?status_message=expired_session")
    uname = request.session.get("uname", None)
    if request.session.get("uname", None) is None:
        print("uname is None :)")
        return HttpResponseRedirect(f"/grizz_bank/login/?status_message=invalid_session")
    context = fetch_acct_data(uname)
    return render(request, "grizz_bank/deposit.html", context)


def delete(request):
    """
    Django view which renders the delete account template.
    :param request: Djanto HTTP GET request
    :return: rendered HTTP response for the delete index
    """
    if "sessionid" not in request.COOKIES or (request.session.get_expiry_age() == 0):
        print("Session not set, or expired")
        return HttpResponseRedirect(f"/grizz_bank/login/?status_message=expired_session")
    uname = request.session.get("uname", None)
    if request.session.get("uname", None) is None:
        print("uname is None :)")
        return HttpResponseRedirect(f"/grizz_bank/login/?status_message=invalid_session")
    context = fetch_acct_data(uname)
    if len(context["account_data"]) <= 1:
        print("User can't delete last account")
        return HttpResponseRedirect(f"/grizz_bank/?status_message=attempt_delete_last_acct")
    # Check if use failed to select the confirm deletion checkbox
    if "err_msg" in request.GET:
        if request.GET["err_msg"] == "confirm_delete":
            context["err_msg"] = "Please Check the box confirming deletion of your account."
        elif request.GET["err_msg"] == "bad_acct_selection":
            context["err_msg"] = """Please select a single account to delete, and a single account to place 
                                    remaining balance into."""
    return render(request, "grizz_bank/delete.html", context)

# ===================== Business Logic Views =====================


@transaction.atomic
def create_client(request):
    """
    Create_client handler which creates a client row in the Client table, new checking and savings account rows
    associated to the new Client row with an initial non-zero balance in the savings account, and balance of $0.00
    in the checking. A password salt and hash are set in the Client row to allow the user to login after this view
    redirects to the Grizz Bank login page. This action is performed as an ACID transaction.
    :param request:
    :return: rendered HTTP response for the delete index
    """
    #creation of salt and hash of password
    chars = []
    for i in range(10):
        chars.append(random.choice(ALPHABET))
    salt = "".join(chars)
    password = request.POST["password"]
    user = request.POST["username"]
    phone = request.POST["phonenumber"]
    emailGiven = request.POST["email"]
    sav_bal = decimal.Decimal(float(request.POST["initialsavingsbalance"]))

    #populate tables: Client, Username_archive, Email_archive, Phone_number_archive
    with transaction.atomic():
        client = Client(f_name = request.POST["firstname"],
                        l_name = request.POST["lastname"],
                        pword_salt = salt,
                        pword_hash = hashlib.sha256(str(password+salt).encode('utf-8')).hexdigest(),
                        email = emailGiven,
                        username = user,
                        phone_number = phone)

    client.save()

    userArchive = UsernameArchive(username = user,
                                  client = client)

    phoneNumberArchive = PhoneNumberArchive(client = client,
                                            phone_number = phone)

    emailArchive = EmailArchive(client = client,
                                email = emailGiven)

    #save all of the data in the tables
    userArchive.save()
    phoneNumberArchive.save()
    emailArchive.save()
    request.session["id"] = client.pk
    new_response = HttpResponse(request)

    #create checking and savings accounts
    chk_account = Account(acct_bal = decimal.Decimal(0),
                          acct_type="C",
                          client=client)
    chk_account.save()

    sav_account = Account(acct_bal = sav_bal,
                          acct_type = "S",
                          client=client)
    sav_account.save()
    return HttpResponseRedirect("/grizz_bank/")


@transaction.atomic
def forgot_password_request_handler(request):
    """
    Take a POST from the forgot password request verification page. Verifies that the verification string submitted
    matches a current row (within 3 mins of reset request) of the ResetRequest page. Updates the client row's salt to
    a new 10char random string, appends it to the new pass word, and hashes it. Updates the Client row's hash to this
    new hash values. This action is performed as an ACID transaction.
    :param request: django HTTP request via POST
    :return: django HTTP redirect
    """
    context = {}
    
    if request.method == 'POST':
        try:
            query = RequestReset.objects.get(reset_id = request.session.get("resetID", None))
            verificationCode = str(request.POST.get('Verify_code'))
            correctVerify=str(query.verification_string)
        except RequestReset.DoesNotExist:
            return HttpResponseRedirect(f"/grizz_bank/login/?&status=Time_EXPIRED")
        if correctVerify == verificationCode:
            print(RequestReset.objects.get(reset_id = request.session.get("resetID", None)))
            print(query.expires)
            dateNow = datetime.datetime.now().replace(tzinfo=utc)
            print(dateNow)
            if (query.expires>= dateNow):
                try:
                    print(request.session.get("uname", None))
                    query = Client.objects.get(username = request.session.get("uname", None))
                    #The password from the user
                    passwordNew=request.POST.get('New_password')
                    passwordConfirm = request.POST.get('confirm_password')
                    #the salt from the database
                    salt = query.pword_salt
                    print(salt)
                    #the salted and hashed password from the database
                    uname = query.username
                except Client.DoesNotExist:
                    return HttpResponseRedirect(f"/grizz_bank/login/?&status=Time_EXPIRED")
                if (passwordNew == passwordConfirm):
                    with transaction.atomic():
                        pwordChange = Client.objects.get(username=uname)
                        newSalt = "".join([random.choice(ALPHABET) for i in range(10)])
                        pwordChange.pword_salt = newSalt
                        pwordChange.pword_hash = hashlib.sha256(str(passwordConfirm+newSalt).encode('utf-8')).hexdigest()
                        pwordChange.save()
                    response = HttpResponseRedirect(f"/grizz_bank/login/?status=FORGOTTON")
                    return response
                else:
                    messages.error(request, 'make sure the new password field matched the confirm new password field')
                    return HttpResponseRedirect(f"/grizz_bank/login/?&status=New_Password_Didnt_Match")
            else:
                messages.error(request, 'incorrect code')
                return HttpResponseRedirect(f"/grizz_bank/login/?&status=Reset_Failed")
                
        return HttpResponseRedirect(f"/grizz_bank/login/?status=TIME_EXPIRED")
    return render(request, "grizz_bank/forgot_password.html", context)


def forgot_password_handler(request):
    """
    Handler for a forgot password post sent from the login page. A RequestReset row is created in the database with
    a verification key, and an email is set to the client's email associated with the account. After creation of the
    RequestReset row, and submission of the email, the user is redirected to the login page.
    :param request: Django POST request
    :return: HTTP GET redirect to login page.
    """
    chars = []
    for i in range(10):
        chars.append(random.choice(ALPHABET))
    verificationKey = "".join(chars)
    date = str(datetime.datetime.now().replace(tzinfo=utc) + timedelta(minutes=3))
    print(date)
    with transaction.atomic():
        ForgotPassword = RequestReset(verification_string = verificationKey,
                                      expires = date)
        ForgotPassword.save()
    resetID = RequestReset.objects.get(verification_string = verificationKey).reset_id
    request.session["resetID"] = resetID
    request.session["uname"] = Client.objects.get(username = request.POST.get('username')).username
    print(request.session.get("resetID", None))
    unameEmail = Client.objects.get(username = request.POST.get('username')).email
    print(resetID)
    print(RequestReset.objects.get(verification_string = verificationKey).expires)
  
    send_mail(
    'GrizzBank Password reset',
    'Your Verification Code:' + RequestReset.objects.get(reset_id = resetID).verification_string + '    Expires in: 3 Minutes',
    'grizzBankNoReply@gmail.com',
    [unameEmail],
    fail_silently=False,
)

    return HttpResponseRedirect(f"/grizz_bank/forgot_password/?status=Email_Sent")


@transaction.atomic()
def reset_password_handler(request):
    """
    Handler view which recieves a POST request from the password reset page. Updates the user's password by generating a
    new random 10-character salt, and hashing with the new password. The Client row for the particular client is updated
    with these new password hash and salt values. This action is performed as an ACID transaction.
    :param request: Django POST request
    :return: http redirect to home page
    """
    context = {}
    print(request.session.get("uname", None))
    query = Client.objects.get(username= request.session.get("uname", None))
    uname = query.username
   
    try:
        if request.method == 'POST':
            print(request.POST)
            print("past IF POST")
            form = AuthenticationForm(request, data=request.POST)
            print(request.POST)
            print(form.is_valid())
            print(form.errors)
            if not form.is_valid():
                #The password from the user
                passwordAttempt=request.POST.get('password')
                #the salt from the database
                salt = query.pword_salt
                print(salt)
                passwordGuess = hashlib.sha256(str(passwordAttempt+salt).encode('utf-8')).hexdigest()
                #the salted and hashed password from the database
                correctPwHash = (query.pword_hash)
                print("correct:", correctPwHash, "   GUESS: ", passwordGuess)
                if (passwordGuess == correctPwHash):
                    passwordNew = request.POST.get('New_password')
                    passwordConfirm = request.POST.get('confirm_password')
                    if (passwordNew == passwordConfirm):
                        with transaction.atomic():
                            pwordChange = Client.objects.get(username=uname)
                            newsalt = "".join([random.choice(ALPHABET) for i in range(10)])
                            pwordChange.pword_salt = newsalt
                            pwordChange.pword_hash = hashlib.sha256(str(passwordConfirm+newsalt).encode('utf-8')).hexdigest()
                            pwordChange.save()
                        response = HttpResponseRedirect(f"/grizz_bank/?uname={uname}&status=Reset_success")
                        return response
                    else:
                        messages.error(request, 'make sure the new password field matched the confirm new password field')
                        return HttpResponseRedirect(f"/grizz_bank/reset_password/?uname={uname}&status=New_Password_Didnt_Match")
                else:
                    messages.error(request, 'incorrect password')
                    return HttpResponseRedirect(f"/grizz_bank/reset_password/?uname={uname}&status=Reset_Failed")
    except Client.DoesNotExist:
        raise RuntimeError("Account not found")
    return render(request, "grizz_bank/index.html", context)


def login_handler(request):
    """
    A handler which view which receives a POST request from the login page containing username and password data.
    Verifies the password matches the hashed value in the Client table row associated with the unique username once
    said password is hashed with salt appended. Set a django session and session cookie in the user's browser
    to keep them logged in.
    :param request:
    :return: HTTP Get redirect to home page or login, depending on login success
    """
    try:
        if request.method == 'POST':
            post = request.POST
            if "username" in post and "password" in post:
                uname = post["username"]
                passwordAttempt= post["password"]
                try:
                    query = Client.objects.get(username=uname)
                except Exception:
                    raise ValueError("username not found")
                #The password from the user
                #the salt from the database
                salt = query.pword_salt
                print("salt", salt)
                passwordGuess = hashlib.sha256(str(passwordAttempt+salt).encode('utf-8')).hexdigest()
                #the salted and hashed password from the database
                correctPwHash = (query.pword_hash)
                print("correct:", correctPwHash)
                print("correct:", correctPwHash, "   GUESS: ", passwordGuess)
                if (passwordGuess == correctPwHash):
                    #login success
                    # Set the uname session value to username the user logged in with
                    if (request.POST.get('remember') == 'on'):
                        print(request.POST.get('remember'))
                        
                        request.session["uname"] = uname
                        request.session.set_expiry(SESSION_EXPIRATION * 60)  # expires in SESSION_EXPIRATION * 60s seconds (Final Suggestion: if remember me is checked we can set session to last mabye 7 days)
                    
                    else:
                        print(request.POST.get('remember'))
                        request.session["uname"] = uname
                        request.session.set_expiry(SESSION_EXPIRATION * 30)  # expires in SESSION_EXPIRATION * 30s seconds (Final Suggestion: if remember me is unchecked we can set session to last 1 day)
                    response = HttpResponseRedirect(f"/grizz_bank/?uname={uname}&status=Login_success")
                    return response
                else:
                    messages.error(request, 'username or password not correct')
                    return HttpResponseRedirect(f"/grizz_bank/login?&status=Login_Failed")
            else:
                return HttpResponseRedirect(f"/grizz_bank/login?&status=not_valid")
        else:
            return HttpResponseRedirect(f"/grizz_bank/login?&status=rediect_not_post")
    except ValueError:
        return HttpResponseRedirect(f"/grizz_bank/login?&status=Account_Not_Found")
    except Exception:
        return HttpResponseRedirect(f"/grizz_bank/login?&status=server_error")


def logout_handler(request):
    """
    Simple handler which logs the user out, flushing the session from the DB and removing the session cookie.
    Redirects to login page.
    :param request: Django request
    :return: HttpRedirectResponse
    """
    if "sessionid" in request.COOKIES:
        request.session.flush()
        return HttpResponseRedirect("../grizz_bank/login/?status_message=logged_out")
    # Client wasn't logged in the first place (session likely already expired)
    return HttpResponseRedirect("../grizz_bank/login/")


@transaction.atomic
def transfer_handler(request):
    """
    Handles incoming POST request sent from the transfer page. Updates the balances of two accounts associated with
    the client logged in, removing the requested amount from the source account, and placing it into the destinaiton
    account. This action is performed as an ACID transaction.
    :param request: POST request with account ids to transfer to, and from, as well as quantities
    :return: HTTP response, or redirect
    """
    uname = ""  # initially set uname to empty string
    try:
        # Check that expected the request was via POST, and correct fields are in the request
        if request.method != "POST":
            raise RuntimeError("Transfer handler expects a post")
        post = request.POST
        for field in ["transfer_amount", "uname"]:
            if field not in post:
                raise RuntimeError(f"Transfer Handler expected the missing field {field} to be in the request.")
        # Retrieve account data from db using data sent by post
        amount, uname = post["transfer_amount"], post["uname"]
        if not (len(amount) > 0 or amount.replace(".", "").isnumeric()):
            raise RuntimeError(f"Transfer handler error: Invalid amount passed by user. amount={amount}")
        # Convert ammount to a decimal type from the string
        amount = decimal.Decimal(float(amount))
        from_id, to_id = get_account_ids(post)
        print(f"amount: {amount}")
        if amount <= 0.0:
            raise RuntimeError(f"transfer handler error: invalid transfer amount. Cannot transfer amount <= 0. amount {amount}")
        from_acct = Account.objects.get(pk=from_id)
        # Check that the account transfering from has enough funds
        from_bal = from_acct.acct_bal
        if from_bal < amount:
            errmsg = f"Transfer Handler error: acct# {from_id} has insufficient funds: {from_acct.acct_bal:.2f} needed {amount:.2f}"
            raise RuntimeError(errmsg)
        to_acct = Account.objects.get(pk=to_id)
        # Check that accounts belong to same user
        acct_id = Client.objects.get(username=uname).client_id
        if to_acct.client.pk != from_acct.client.pk or to_acct.client.pk != acct_id or from_acct.client.pk != acct_id:
            print(f"acct_id: {acct_id} from_client_id: {from_acct.client.pk} to_client_id: {to_acct.client.pk}")
            raise RuntimeError(f"Transfer Handler error: account owner mismatch: from owner ID: {from_acct.client} to owner id:{to_acct.client}")
        # Perform the transfer as an ACID transaction
        with transaction.atomic():
            from_acct.acct_bal -= amount
            to_acct.acct_bal += amount
            from_acct.save()
            to_acct.save()
        # transfer successfully occurred
        return HttpResponseRedirect(f"/grizz_bank?uname={uname}&status=transfer_success")

    except IntegrityError as e:
        print(e)
        print(f"POST data: {post}")
        return HttpResponseRedirect(f"/grizz_bank/transfer/?uname={uname}&error_msg=transfer_transaction_error")
    except RuntimeError as e:
        print(e)
        print(f"POST data: {post}")
        return HttpResponseRedirect(f"/grizz_bank/transfer/?uname={uname}&error_msg=transfer_invalid_transfer_error")
    except Exception as e:
        print(e)
        print(f"Post data: {post}")
        return HttpResponseRedirect(f"/grizz_bank/transfer/?uname={uname}&error_msg=unknown_transfer_error")


@transaction.atomic
def deposit_handler(request):
    """
    Handles incoming POST Requests sent from the deposit page. Updates the balance in the destination account associated
    with and selected by the client (eg their savings account w/ ID=15). Currently simulates checking the validity of
    the check submitted by making sure the string "invalid" is NOT in the image filename.
    This action is performed as an ACID transaction.
    :param request: HTTP POST request with
    :return: HTTP Redirect to index page
    """
    try:
        for key in ["uname", "deposit_amount"]:
            if key not in request.POST:
                raise KeyError(f"Deposit handler error: POST request missing {key} value")
        if "check_img" not in request.FILES:
            raise KeyError(f"Deposit handler error: POST request missing the check image")
        uname, check_img, amount = request.POST["uname"], request.FILES["check_img"], request.POST["deposit_amount"]
        # In lieu of a computer vision call to verify check is valid and matches amount specified, reject if
        # "invalid" is part of the filename
        if "invalid" in check_img.name.lower():
            raise ValueError(f"Deposit handler error: Invalid check submitted")
        elif not amount.replace(".", "").isnumeric():
            raise ValueError(f"Deposit handler error: Invalid deposit amount {amount}")
        amount = decimal.Decimal(float(amount))
        # Get the account id
        id = get_acct_id(request.POST.keys())
        if id == -1:
            raise KeyError(f"Deposit handler error: No account selected as deposit destination")
        # Perform the transfer as an ACID transaction
        with transaction.atomic():
            dest_acct = Account.objects.get(pk=id)
            dest_acct.acct_bal += amount
            dest_acct.save()
            # transfer successfully occurred
        return HttpResponseRedirect(f"/grizz_bank/?uname={request.POST['uname']}&status_msg=deposit_success")
    except KeyError as e:
        print(e)
        print(f"Post data: {request.POST}")
        return HttpResponseRedirect(f"/grizz_bank/deposit/?uname={request.POST['uname']}&error_msg=invalid_input_error")
    except ValueError as e:
        print(e)
        print(f"Post data: {request.POST}")
        return HttpResponseRedirect(f"/grizz_bank/deposit/?uname={request.POST['uname']}&error_msg=bad_value_error")
    except IntegrityError as e:
        print(e)
        print(f"POST data: {request.post}")
        return HttpResponseRedirect(f"/grizz_bank/deposit/?uname={uname}&error_msg=deposit_transaction_error")
    except Exception as e:
        print(e)
        print(f"Post data: {request.POST}")
        return HttpResponseRedirect(f"/grizz_bank/deposit/?uname={request.POST['uname']}&error_msg=unknown_error")


def create_savings(request):
    """To be implemented in future to allow clients to add new savings accounts"""
    pass

    #populate tables: Account and Interest Rate
def create_checking(request):
    """to be implemented in future to allow users to add new checking accounts"""
    pass

@transaction.atomic
def delete_handler(request):
    """
    Django view which handles business logic for the deletion of a bank account. Deletes and account and transfers the
    balance which remained inside the deleted account into a destination account owned by the same cliernt.
    This action is performed as an ACID transaction.
    :param request:
    :return:
    """
    if request.method == "POST":
        try:
            print("post:", request.POST)
            uname = request.session.get("uname")
            from_id, to_id = get_account_ids(request.POST)
            # Can't deposit into same acct your are deleting
            if from_id == to_id:
                return HttpResponseRedirect("./err_msg=bad_acct_Selection")
            elif "confirm_delete" not in request.POST or request.POST["confirm_delete"] != "on":
                raise ValueError("User didn't confirm acct deletion")
            client_id = Client.objects.get(username=uname).client_id
            to_delete = Account.objects.get(pk=from_id)
            transfer_to = Account.objects.get(pk=to_id)
            if client_id == to_delete.client.pk == transfer_to.client.pk:
                # all good to perform the delete transaction
                with transaction.atomic():
                    remaining_bal = to_delete.acct_bal
                    transfer_to.acct_bal += remaining_bal
                    to_delete.delete()
                    transfer_to.save()
            else:
                msg = "Somehow account to delete and account to deposit to did not have same key as client " + \
                        f"\n\tclient id:{client_id}" + f" delete id: {to_delete.pk}" + f" dest id: {from_id}"
                raise Exception(msg)
            return HttpResponseRedirect("../grizz_bank/?status_msg=successful_deletion")
        except ValueError as e:
            print(e)
            return HttpResponseRedirect("./delete/?err_msg=confirm_delete")
        except RuntimeError as e:
            print(e)
            return HttpResponseRedirect("./delete/?err_msg=bad_acct_selection")
        except Exception as e:
            print(e)
            return HttpResponseRedirect("./delete/?err_msg=unkown_delete_err")
    else:
        print(f"Attempted acces sof delete_handler via invalid thing")
        return HttpResponseRedirect("../grizz_bank/")



# View Helper Functions for use in multiple views

def create_account_data_list(accounts):
    """
    Helper function which transforms data from a Django Account row object into a list of python dictionaries
    containing account data (type, balance, id)
    rendering in the template.
    :param accounts: list of Account row objects
    :return: python dictionary
    """
    # dictionary mapping account type key to an actual account type name
    types = {"S": "Savings", "C": "Checking"}
    # List comprehension returning a list of dictionaries containing account type, balance, and ID
    acct_data = [{"type": types[acct.acct_type], "bal": acct.acct_bal, "id": acct.acct_id} for acct in accounts]
    return acct_data


def fetch_acct_data(uname):
    """
    Helper function which retrieves savings/checking accounts, from the database, and stores them in a
    dicitonary which can be used as a django context for template rendering. Used by various vierws rendering
    templates w/ account balances.
    :param uname: string
    :return: python dictionary
    """
    acct_data = {}
    try:
        client_id = Client.objects.get(username=uname).client_id
        client_accounts = Account.objects.filter(client_id=client_id)
        # List comprehension to build a list of python dictionaries containing account data into the context
        acct_data["account_data"] = create_account_data_list(client_accounts)
        acct_data["uname"] = uname
        acct_data["error"] = False
    except Exception as e:
        # If an error happens log to console, set context error flag true, and make account data an empty list
        print(e)
        acct_data["error"] = True
        acct_data["account_data"] = list()

    return acct_data


def get_acct_id(post_keys):
    """
    Helper function which takes in an iterable of keys in a POST request, and returns the account key of the
    savings or checking account within the keys if one exists. Return -1 if no account found
    :param post_keys: iterable of key values from a POST request dictionary
    :return: account id as an integer, -1 if DNE
    """
    for k in post_keys:
        print(f"type of key: {type(k)}")
        res = re.match("(del)|(to)|(from)_acct", k)
        if res is not None:
            return int(k.split("acct")[1])
    return -1


def get_account_ids(post_dict):
    """
    Helper function extracting the acount ids from the POST request's keys
    :param post_dict: python dictionary
    :return: (int: from_id, int: to_id)
    """
    from_id, to_id = None, None
    for key in post_dict.keys():
        from_match = re.match("from_acct\d*", key)
        to_match = re.match("to_acct\d*", key)
        # matches can have the id extracted by splitting string on "acct" substring and selecting second half
        if from_match is not None:
            from_id = int(from_match.string.split("acct")[1])
            continue
        if to_match is not None:
            to_id = int(to_match.string.split("acct")[1])
    if (from_id is None) or (to_id is None):
        raise RuntimeError("transfer handler error: no valid to/from account IDs found")
    return from_id, to_id


def logout(http_request, status_message=None):
    """
    Implement a logout routine which deletes a user's session, and their
    sessionid in their cookies. Returns an HttpResponseRedirect to login page.
    :param http_request: Django Request object
    :param status_message: string to be made as a status message in GET request
    :return: HttpResponseRedirect
    """
    if "sesisonid" in http_request.COOKIES:
        http_request.session.flush()
    if status_message is None:
        return HttpResponseRedirect("grizz_bank/login/")
    return HttpResponseRedirect(f"grizz_bank/login/?status_message={status_message}")
