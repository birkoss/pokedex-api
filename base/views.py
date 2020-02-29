from django.shortcuts import render

def login(request):

	return render(request, "base/login.html")


def register(request):

	return render(request, "base/register.html")


def forgot_password(request):

	return render(request, "base/forgot_password.html")