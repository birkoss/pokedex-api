from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect

from social_django.models import UserSocialAuth


def error_404(request, exception=None):
	return render(request, 'base/404.html')


@login_required
def user_logout(request):
	logout(request)

	return redirect('pokemon_archive')


@login_required
def user_filters(request):
	if request.method == "POST":
		cookie_name = request.POST.get("type", "")
		cookie_values = request.POST.getlist("values[]", [])

		response = {}

		if cookie_name == "":
			response['status'] = "error"
			response['msg'] = "The filter and its values are mandatory!"
			return JsonResponse(response)

		request.session[cookie_name] = cookie_values

		response['status'] = 'ok'

		return JsonResponse(response)
	else:
		pokemon_hide = request.session.get("hide", [])
		return render(request, 'base/modal_filters.html', {
			"hide": pokemon_hide
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