from django.shortcuts import render


def clocking_page(request, public_uuid: str):
    return render(request, "employee/pages/clocking.html", {"public_uuid": public_uuid})
