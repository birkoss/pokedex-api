from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect

from social_django.models import UserSocialAuth


def error_404(request, exception=None):
	return render(request, 'base/404.html')


def contact(request):
	return render(request, 'base/contact.html')


@login_required
def user_logout(request):
	logout(request)

	return redirect('pokemon_archive')


@login_required
def user_filters(request):
	if request.method == "POST":
		setting_name = request.POST.get("type", "")
		setting_value = ""

		if 'value' in request.POST:
			setting_value = request.POST.get("value", "")
		else:
			setting_value = request.POST.getlist("values[]", [])

		response = {}

		if setting_name == "":
			response['status'] = "error"
			response['msg'] = "The filter and its values are mandatory!"
			return JsonResponse(response)

		request.session[setting_name] = setting_value

		response['status'] = 'ok'

		return JsonResponse(response)
	else:
		pokemon_hide = request.session.get("hide", [])
		return render(request, 'base/modal_filters.html', {
			"current_filters": pokemon_hide
		})


@login_required
def user_profile(request):
	user = request.user

	try:
		github_login = user.social_auth.get(provider='github')
	except UserSocialAuth.DoesNotExist:
		github_login = None

	try:
		google_login = user.social_auth.get(provider='google-oauth2')
	except UserSocialAuth.DoesNotExist:
		google_login = None

	try:
		facebook_login = user.social_auth.get(provider='facebook')
	except UserSocialAuth.DoesNotExist:
		facebook_login = None

	can_disconnect = (user.social_auth.count() > 1)

	return render(request, 'base/profile.html', {
		'github_login': github_login,
		'google_login': google_login,
		'facebook_login': facebook_login,
		'can_disconnect': can_disconnect
	})