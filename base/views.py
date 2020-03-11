from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect

from social_django.models import UserSocialAuth

import json


def error_404(request, exception=None):
	return render(request, 'base/404.html')


def contact(request):
	return render(request, 'base/contact.html')


@login_required
def user_logout(request):
	logout(request)
	return redirect('pokemon_archive')


@login_required
def user_settings(request):
	if request.method == "POST":
		settings = {}

		try:
			settings = json.loads(request.POST.get("settings", {}))
		except json.decoder.JSONDecodeError:
			pass

		for single_setting in settings:
			request.session[single_setting] = settings[single_setting]
		
		response = {}

		response['status'] = 'ok'

		return JsonResponse(response)
	else:
		filters = request.session.get("filters", [])
		language = request.session.get("language", "en")
		return render(request, 'base/modal_settings.html', {
			"current_filters": filters,
			"current_language": language
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