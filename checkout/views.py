from django.shortcuts import render, redirect, reverse, HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.sites.models import Site
from django.conf import settings
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import stripe
import datetime
from photos.models import Photo
from customers.models import Customer, Download

endpoint_secret = settings.SIGNING_SECRET


@login_required
def checkout(request):
    # get stripe api key from environment variable
    stripe.api_key = settings.STRIPE_SECRET_KEY

    # retrieve cart from session
    cart = request.session.get('shopping_cart', {})

    line_items = []

    # append cart items into line items for stripe
    for id, photo in cart.items():
        try:
            photo_object = Photo.objects.get(id=id)
        except ObjectDoesNotExist:
            photo_object = None

        line_items.append({
            'name': photo_object.caption,
            'amount': int(photo_object.price*100),
            'currency': 'usd',
            'quantity': 1
        })

    current_site = Site.objects.get_current()
    domain = current_site.domain

    # create checkout session object
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=line_items,
        success_url=domain + reverse(checkout_success),
        cancel_url=domain + reverse(checkout_cancelled),
    )

    session['success_url'] = session['success_url']+ f'?session_id={session.id}'
    request.session['checkout_session_id'] = session.id

    return render(request, 'checkout/checkout.template.html', {
        'session_id': session.id,
        'public_key': settings.STRIPE_PUBLISHABLE_KEY
    })


@login_required
def checkout_success(request):

    # verify if checkout session id is in url
    session_id_in_url = request.GET.get('session_id', '')

    if session_id_in_url:
        if session_id_in_url == request.session['checkout_session_id']:

            cart = request.session['shopping_cart']
            customer = Customer.objects.get(user=request.user)

            # write cart items into database to enable user to download
            for id, photo in cart.items():
                try:
                    photo_object = Photo.objects.get(id=id)
                except ObjectDoesNotExist:
                    photo_object = None

                new_download = Download(
                    user = customer,
                    image = photo_object,
                    size = photo['size'],
                    date = datetime.datetime.now(),
                    )
                new_download.save()

            # Empty the shopping cart
            request.session['shopping_cart'] = {}
            messages.success(request, "Thank you for your payment. You may download the images now.")

            return render(request, 'checkout/checkout_success.template.html', {
                'cart': cart
            })
        else:
            raise PermissionDenied
    else:
        raise PermissionDenied


@login_required
def checkout_cancelled(request):
    messages.error(request, "Payment has been cancelled.")

    return redirect(reverse('view_cart'))


@login_required
@csrf_exempt
def payment_completed(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValuedError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_session(session)

    return HttpResponse(status=200)


@login_required
def handle_checkout_session(session):
    print(session)

