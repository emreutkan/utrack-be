from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.apple.views import AppleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView

class AppleOAuth2Client(OAuth2Client):
    def __init__(self, **kwargs):
        self.scope_delimiter = kwargs.pop('scope_delimiter', ' ')
        super().__init__(**kwargs)

class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client
    # callback_url is not needed for mobile 'id_token' flow usually, 
    # but if it errors, set it to: callback_url = "http://localhost:8000"

class AppleLogin(SocialLoginView):
    adapter_class = AppleOAuth2Adapter
    client_class = AppleOAuth2Client
    callback_url = "https://example.com" # Dummy URL required for Apple
