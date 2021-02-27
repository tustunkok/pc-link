from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from accounts.forms import *
from pc_calculator.forms import StudentBulkUploadForm
from django.contrib.auth import views as auth_views

def register(request):
    if request.method == 'POST':
        user_creation_form = UserRegisterForm(request.POST)
        if user_creation_form.is_valid():
            user_creation_form.save()
            messages.success(request, 'Your account has been created. You are now able to log in.')
            return redirect('login')
    else:
        user_creation_form = UserRegisterForm()
    return render(request, 'accounts/register.html', {'form': user_creation_form})


@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your profile is updated.')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
        stu_bulk_form = StudentBulkUploadForm()
    
    context = {
        'u_form': u_form,
        'p_form': p_form,
        'stu_bulk_form': stu_bulk_form,
    }

    return render(request, 'accounts/profile.html', context)
