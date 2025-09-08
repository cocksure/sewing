from django.shortcuts import render


def handler403(request, exception=None, template_name="403.html"):
    return render(request, template_name, status=403)


def handler404(request, exception=None, template_name="404.html"):
    return render(request, template_name, status=404)


def handler500(request, template_name="500.html"):
    # у 500 нет exception
    return render(request, template_name, status=500)
