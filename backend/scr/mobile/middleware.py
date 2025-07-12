import re
from django.http import HttpResponseRedirect
from django.urls import reverse, NoReverseMatch
from django.conf import settings
import logging
from urllib.parse import quote as urlquote # Python標準ライブラリのquoteをurlquoteとしてインポート

# Get an instance of a logger
logger = logging.getLogger(__name__)

# A list of common mobile user agent patterns
# This list can be expanded for more comprehensive detection
MOBILE_USER_AGENT_PATTERNS = [
    r'Mobi', r'Android', r'iPhone', r'iPad', r'iPod',
    r'Opera Mini', r'Windows Phone', r'BlackBerry',
    r'webOS', r'Kindle', r'Nokia', r'SonyEricsson',
    r'HTC', r'Samsung', r'LG', r'Motorola',
]
MOBILE_REGEX = re.compile(r'|'.join(MOBILE_USER_AGENT_PATTERNS), re.IGNORECASE)

# Default mobile path prefix if not set in settings
# This should match the prefix used in your main urls.py for the mobile app
DEFAULT_MOBILE_PATH_PREFIX = '/mobile/'

# Paths that should not trigger a redirect to the mobile site
# even if accessed by a mobile device.
# These should be absolute paths starting with '/'
DEFAULT_NON_REDIRECT_PREFIXES = [
    '/admin/',
    '/api/',
    '/users/login/',
    '/users/logout/',
    '/users/password_change/',
    '/users/password_change/done/',
    '/__debug__/', # Django Debug Toolbar
]

class AutoMobileRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Use a specific setting for the mobile app's URL prefix or a default
        self.mobile_path_prefix = getattr(settings, 'MOBILE_APP_URL_PREFIX', DEFAULT_MOBILE_PATH_PREFIX).rstrip('/') + '/'
        # Ensure the prefix starts with a slash
        if not self.mobile_path_prefix.startswith('/'):
            self.mobile_path_prefix = '/' + self.mobile_path_prefix
        
        # Use a specific setting for excluded prefixes or defaults
        self.non_redirect_prefixes = getattr(settings, 'MOBILE_REDIRECT_EXCLUDE_PREFIXES', DEFAULT_NON_REDIRECT_PREFIXES)
        # URL name to redirect desktop users to if they land on a mobile page
        self.desktop_redirect_url_name = getattr(settings, 'DESKTOP_REDIRECT_URL_NAME', 'main')

        # Get the path for the desktop login URL
        try:
            # settings.LOGIN_URL is typically a URL name like 'users_login'
            self.desktop_login_path = reverse(settings.LOGIN_URL)
        except AttributeError: # LOGIN_URL not in settings
            logger.warning("settings.LOGIN_URL is not defined. Assuming '/users/login/' for desktop login path.")
            self.desktop_login_path = '/users/login/' # Fallback
        except NoReverseMatch: # LOGIN_URL is defined but not reversible
            logger.warning(
                f"Could not reverse settings.LOGIN_URL ('{settings.LOGIN_URL}'). "
                f"Assuming it's a direct path. Mobile login redirect might be affected if it's incorrect."
            )
            self.desktop_login_path = settings.LOGIN_URL # Assume it's a literal path

    def __call__(self, request):
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        current_path_full = request.path # Keep original for logging/display
        current_path_normalized = request.path.rstrip('/') # For comparison
        is_mobile_device = bool(user_agent and MOBILE_REGEX.search(user_agent))

        # 1. AJAX requests should generally not be redirected
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return self.get_response(request)

        # 2. Handle redirection for DESKTOP users on MOBILE pages
        if not is_mobile_device and current_path_normalized.startswith(self.mobile_path_prefix.rstrip('/')):
            # Desktop user is on a mobile-specific page.
            # Check if this specific mobile path is an exception (e.g., part of non_redirect_prefixes)
            # This allows, for example, /mobile/api/ to be accessible by anyone if listed in non_redirect_prefixes.
            for prefix in self.non_redirect_prefixes:
                if current_path_normalized.startswith(prefix.rstrip('/')):
                    logger.debug(
                        f"Desktop user on mobile path '{current_path_full}' which is an excluded prefix '{prefix}'. No redirect."
                    )
                    return self.get_response(request)

            try:
                desktop_target_url = reverse(self.desktop_redirect_url_name)
                # Prevent redirect loop if the desktop target URL somehow points back to a mobile page
                if not desktop_target_url.rstrip('/').startswith(self.mobile_path_prefix.rstrip('/')):
                    logger.info(f"Desktop user on mobile page '{current_path_full}'. Redirecting to '{desktop_target_url}'.")
                    return HttpResponseRedirect(desktop_target_url)
                else:
                    logger.warning(
                        f"AutoMobileRedirectMiddleware: Desktop redirect URL '{desktop_target_url}' "
                        f"for path '{current_path}' starts with mobile prefix '{self.mobile_path_prefix}'. "
                        "Avoiding potential redirect loop. Request will proceed."
                    )
            except NoReverseMatch:
                logger.error(
                    f"AutoMobileRedirectMiddleware: Could not reverse '{self.desktop_redirect_url_name}' for desktop redirect. "
                    "Please check your URL configuration. Request will proceed."
                )
            # If redirect fails or is unsafe, let the desktop user see the mobile page rather than erroring.
            return self.get_response(request)

        # 3. Handle redirection for MOBILE users
        if is_mobile_device:
            # PRIORITY 1: If mobile user hits the DESKTOP login page, redirect to MOBILE login page.
            # Ensure desktop_login_path is not None and is a string before rstrip
            desktop_login_path_normalized = self.desktop_login_path.rstrip('/') if isinstance(self.desktop_login_path, str) else None

            if desktop_login_path_normalized and current_path_normalized == desktop_login_path_normalized:
                try:
                    mobile_login_url = reverse('mobile:login')
                    next_param = request.GET.get('next')
                    final_next_path = ''

                    if next_param:
                        # If 'next' is a desktop page, new 'next' for mobile login should be mobile:index
                        # or a mapped mobile equivalent. For simplicity, use mobile:index.
                        if not next_param.startswith(self.mobile_path_prefix):
                            try:
                                final_next_path = reverse('mobile:index')
                            except NoReverseMatch:
                                final_next_path = self.mobile_path_prefix # Fallback
                        else:
                            final_next_path = next_param # Already a mobile path
                    else: # No 'next' provided, default to mobile index after login
                        try:
                            final_next_path = reverse('mobile:index')
                        except NoReverseMatch:
                            final_next_path = self.mobile_path_prefix
                    
                    redirect_url_for_mobile_login = mobile_login_url
                    if final_next_path:
                         redirect_url_for_mobile_login = f"{mobile_login_url}?next={urlquote(final_next_path)}"

                    logger.info(
                        f"Mobile user on desktop login '{current_path_full}'. Redirecting to mobile login '{redirect_url_for_mobile_login}'."
                    )
                    return HttpResponseRedirect(redirect_url_for_mobile_login)
                except NoReverseMatch:
                    logger.error("AutoMobileRedirectMiddleware: 'mobile:login' URL not found. Mobile user might see desktop login page.")
                    # Fall through to allow access to desktop login if mobile:login is broken

            # PRIORITY 2: If already on a mobile page (and not the desktop login page handled above).
            if current_path_normalized.startswith(self.mobile_path_prefix.rstrip('/')):
                return self.get_response(request)

            # PRIORITY 3: Check non-redirect prefixes (e.g., /admin/, /api/).
            # The desktop login path was handled by PRIORITY 1, so even if it's in
            # NON_REDIRECT_PREFIXES, mobile users get the special redirect.
            # Other prefixes in NON_REDIRECT_PREFIXES will allow mobile users to access them.
            for prefix in self.non_redirect_prefixes:
                if current_path_normalized.startswith(prefix.rstrip('/')):
                    return self.get_response(request)

            # PRIORITY 4: Mobile user on a desktop page (that's not login and not excluded).
            # Redirect to the mobile site's index page.
            try:
                mobile_target_url = reverse('mobile:index')
                logger.info(f"Mobile user on desktop page '{current_path_full}'. Redirecting to '{mobile_target_url}'.")
                return HttpResponseRedirect(mobile_target_url)
            except NoReverseMatch:
                logger.error("AutoMobileRedirectMiddleware: Could not reverse 'mobile:index'. Request will proceed.")
                # Proceed without redirecting to avoid breaking the site if 'mobile:index' is misconfigured.
                return self.get_response(request)

        # If not a mobile device and not on a mobile page (i.e., desktop user on desktop page)
        # or if any of the above conditions led to falling through.
        return self.get_response(request)
