from django.shortcuts import render, redirect
from django.http import Http404
from django.views import View
from apps.common.models import Business


class ClockingView(View):
    """Renders the screen necessary for the employee to clock in."""

    def get(self, request, public_uuid: str):
        business = Business.objects.filter(public_uuid=public_uuid).first()
        if not business:
            raise Http404()
        return render(
            request,
            "employee/pages/clocking.html",
            {"public_uuid": business.public_uuid},
        )


class ShortLinkView(View):
    """Shorten the company page link and redirect it."""

    def get(self, request, code: str):
        business = Business.objects.filter(short_link=code).first()
        if not business:
            raise Http404()
        return redirect("page-employee:clocking", public_uuid=business.public_uuid)
