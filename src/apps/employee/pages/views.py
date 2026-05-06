from django.shortcuts import render, redirect
from django.http import Http404
from apps.common.models import Business


def clocking_view(request, public_uuid: str):
    """Renders the screen necessary for the employee to clock in."""
    business = Business.objects.filter(public_uuid=public_uuid).first()
    if not business:
        raise Http404()
    return render(
        request,
        "employee/pages/clocking.html",
        {"public_uuid": business.public_uuid},
    )


def short_link_view(request, code: str):
    """Shorten the company page link and redirect it."""
    business = Business.objects.filter(short_link=code).first()
    if not business:
        raise Http404()
    return redirect("page-employee:clocking", public_uuid=business.public_uuid)
