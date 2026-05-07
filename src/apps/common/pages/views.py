from django.views import View
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render


class RegisterView(View):
    def get(self, request):
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("login")
        else:
            form = UserCreationForm()
        return render(request, "registration/register.html", {"form": form})
