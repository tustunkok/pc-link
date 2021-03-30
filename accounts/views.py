"""
PÇ-Link is a report creation software for MÜDEK.
Copyright (C) 2021  Tolga ÜSTÜNKÖK

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from accounts.forms import *
from pc_calculator.forms import StudentBulkUploadForm
from django.contrib.auth import views as auth_views
from django.conf import settings

def register(request):
    with open(settings.BASE_DIR / 'registration_state.txt', 'r') as reg_f:
        reg_enabled = bool(int(reg_f.read()))

    if reg_enabled:
        if request.method == 'POST':
            user_creation_form = UserRegisterForm(request.POST)
            if user_creation_form.is_valid():
                user_creation_form.save()
                messages.success(request, 'Your account has been created. You are now able to log in.')
                return redirect('login')
        else:
            user_creation_form = UserRegisterForm()
        return render(request, 'accounts/register.html', {'form': user_creation_form})
    else:
        messages.warning(request, 'Registrations to PÇ-Link are closed.')
        return redirect('login')


@login_required
@staff_member_required
def toggle_registrations(request):
    with open(settings.BASE_DIR / 'registration_state.txt', 'r+') as reg_f:
        reg_enabled = bool(int(reg_f.read()))
        reg_f.seek(0)
        reg_f.write(str(int(not reg_enabled)))
        messages.success(request, 'Registration status: ' + str(not reg_enabled))

    return redirect('profile')

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
    
    with open(settings.BASE_DIR / 'registration_state.txt', 'r') as reg_f:
        reg_enabled = bool(int(reg_f.read()))
    
    context = {
        'u_form': u_form,
        'p_form': p_form,
        'stu_bulk_form': stu_bulk_form,
        'reg_status': reg_enabled
    }

    return render(request, 'accounts/profile.html', context)
