from django.shortcuts import render, redirect, reverse
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomerForm
from .models import Customer, Download, Favourite
from photos.models import Photo


def check_user_in_group(user):

    # return True if user is in group 'customers'
    customer_group = Group.objects.get(name='customers')
    if customer_group in user.groups.all():
        return True
    else:
        return False


def get_customer(user):

    # return customer object if found else return None
    try:
        customer = Customer.objects.get(user=user)
    except ObjectDoesNotExist:
        customer = None

    return customer


@login_required
def create_profile(request):

    # check if user is in group 'customers'
    is_customer = check_user_in_group(request.user)

    # get customer object from Customer model if user is in customer group
    if is_customer:

        customer = get_customer(request.user)

        # if customer has already created a profile,
        # redirect customer to view profile page
        # else display form to create profile
        if customer:
            return redirect(reverse(view_profile))

        else:

            # if user has submitted the form
            if request.method == "POST":
                create_form = CustomerForm(request.POST)

                # check if form is valid, add to database if valid
                if create_form.is_valid():
                    profile = create_form.save(commit=False)
                    profile.user = request.user
                    profile.save()
                    messages.success(
                        request,
                        "Profile created successfully."
                    )
                    return redirect(reverse(view_profile))

                else:
                    # if form is not valid, display error message
                    # and render the form again
                    messages.error(
                        request,
                        "Error, please check your form and resubmit"
                    )

                    return render(
                        request,
                        'customers/create_profile.template.html',
                        {
                            'form': create_form
                        })

            else:
                # if user has not submitted any form, render an empty form
                form = CustomerForm()

                return render(
                    request,
                    'customers/create_profile.template.html',
                    {
                        'form': form
                    })
    else:
        # raise permission denied error if user is not in group 'customers'
        raise PermissionDenied


@login_required
def view_profile(request):
    # check if user is in group 'customers'
    is_customer = check_user_in_group(request.user)

    # if customer is in group 'customers'
    if is_customer:

        user_info = request.user
        # get customer profile
        profile = get_customer(user_info)

        return render(request, 'customers/profile.template.html', {
            'profile': profile,
            'user_info': user_info
        })
    else:
        # raise permission denied error if user is not in group 'customers'
        raise PermissionDenied


@login_required
def update_profile(request):

    # check if user is in group 'customers'
    is_customer = check_user_in_group(request.user)

    # if customer is in group 'customers'
    if is_customer:
        # get customer profile
        profile = get_customer(request.user)

        # if user has submitted a form
        if request.method == 'POST':
            # create form object with posted information
            profile_form = CustomerForm(request.POST, instance=profile)

            # if form has no errors
            if profile_form.is_valid():
                # update the profile of the user instance
                profile_form.save()
                return redirect(reverse(view_profile))
            else:
                return render(
                    request,
                    'customers/update_profile.template.html',
                    {
                        'form': profile_form
                    })
        else:
            # if user has not submitted any form
            # retrieve and display data in the rendered form
            profile_form = CustomerForm(instance=profile)
            return render(request, 'customers/update_profile.template.html', {
                'form': profile_form
            })
    else:
        # raise permission denied if user is not in group 'customers'
        raise PermissionDenied


@login_required
def view_download(request):

    is_customer = check_user_in_group(request.user)

    if is_customer:
        customer = get_customer(request.user)
        if customer:
            downloads = Download.objects.filter(user=customer)
        else:
            downloads = None
        return render(request, 'customers/download.template.html', {
            'downloads': downloads
        })
    else:
        raise PermissionDenied


@login_required
def add_to_favourite(request, photo_id):

    # when user click on the heart button
    # this function will check if the photo has been favourited before

    # check if user is a customer
    is_customer = check_user_in_group(request.user)

    # if user is a customer
    if is_customer:
        # get customer profile
        customer = get_customer(request.user)
        if customer:
            # get object of the selected photo
            photo = Photo.objects.get(id=photo_id)
            # get favourited photos of the login user
            customer_favourite = Favourite.objects.filter(user=customer)

            try:
                favourited = customer_favourite.get(image=photo)
            except ObjectDoesNotExist:
                favourited = None

            if favourited is None:
                # if the photo is not added to favourite before,
                # create a new record in database
                new_favourite = Favourite(
                    user=customer,
                    image=photo
                )
                new_favourite.save()
                messages.success(
                    request,
                    f"{photo.caption} has been added to your favourite"
                    )

            else:
                # if the photo is already in database,
                # remove the record from database
                messages.success(
                    request,
                    f"{photo.caption} has been removed from your favourite"
                    )
                favourited.delete()

            # get the url for redirection
            redirect_url = request.POST['redirect_url']

            return redirect(redirect_url)
        else:
            messages.error(
                request,
                'Complete your profile so that you add photos to Favourites'
                )
            return redirect(create_profile)
    else:
        raise PermissionDenied


@login_required
def view_favourites(request):

    # check if user is a customer
    is_customer = check_user_in_group(request.user)

    # if user is a customer
    if is_customer:

        customer = get_customer(request.user)
        if customer:
            favourites = Favourite.objects.filter(user=customer)
        else:
            favourites = None

        return render(request, 'customers/view_favourite.template.html', {
            'favourites': favourites
        })
    else:
        raise PermissionDenied
