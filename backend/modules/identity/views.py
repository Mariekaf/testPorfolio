import logging
from datetime import timedelta
from urllib.parse import urlencode
import uuid

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sessions.models import Session
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from modules.accounts.services import ensure_personal_account, AccountInconsistent
from .models import AuthSession
from .rate_limits import RateLimited, limit_request
from .serializers import EmailSerializer, LoginSerializer, RegistrationSerializer, ResetConfirmSerializer

logger = logging.getLogger('identity.mail')
RESET_MESSAGE = 'Si un compte correspond à cette adresse, un lien de réinitialisation sera envoyé.'
INVALID_RESET = 'Ce lien est invalide ou a expiré. Demandez un nouveau lien.'


def error_response(code, message, status=400, fields=None):
    error = {'code': code, 'message': message}
    if fields:
        error['fields'] = fields
    return Response({'error': error}, status=status)


def csrf_failure(request, reason=''):
    response = JsonResponse({'error': {'code': 'csrf_failed', 'message': 'La vérification de sécurité a échoué. Actualisez la page.'}}, status=403)
    response['Cache-Control'] = 'no-store'
    return response


def serialize_session(request):
    user = request.user
    return {'user': {'id': str(user.pk), 'email': user.email, 'first_name': user.first_name, 'last_name': user.last_name},
            'expires_at': request.session.get_expiry_date().isoformat()}


@method_decorator(never_cache, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
@method_decorator(sensitive_post_parameters('*'), name='dispatch')
class AuthView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [SessionAuthentication]

    def handle_exception(self, exc):
        if isinstance(exc, RateLimited):
            response = error_response('rate_limited','Trop de tentatives. Réessayez plus tard.',429)
            response['Retry-After'] = str(exc.seconds)
            return response
        from rest_framework.exceptions import ValidationError, ParseError, UnsupportedMediaType
        if isinstance(exc, (ValidationError, ParseError, UnsupportedMediaType)):
            return error_response('validation_error','Vérifiez les informations du formulaire.',400,exc.detail if isinstance(exc,ValidationError) else None)
        return super().handle_exception(exc)


class CsrfView(AuthView):
    def get(self, request):
        return Response({'csrf_token': get_token(request)})


class RegisterView(AuthView):
    def post(self, request):
        limit_request(request, 'register')
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        value = serializer.validated_data
        try:
            with transaction.atomic():
                user = get_user_model().objects.create_user(email=value['email'],password=value['password'],first_name=value['first_name'],last_name=value['last_name'])
                ensure_personal_account(user)
        except AccountInconsistent:
            return error_response('account_inconsistent','La création du compte ne peut pas être finalisée.',409)
        except IntegrityError as exc:
            constraint = getattr(getattr(exc.__cause__, 'diag', None), 'constraint_name', '') or ''
            if 'email' not in constraint:
                return error_response('provisioning_unavailable','La création du compte est temporairement indisponible.',503)
            return error_response('validation_error','Cette adresse e-mail ne peut pas être utilisée.',400,{'email':['Cette adresse e-mail est déjà utilisée.']})
        # No automatic session, no email or password returned.
        return Response({'message':'Compte créé. Vous pouvez maintenant vous connecter.'}, status=201)


class LoginView(AuthView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        value = serializer.validated_data
        limit_request(request, 'login', value['email'])
        user = authenticate(request=request._request, email=value['email'], password=value['password'])
        if user is None:
            return error_response('invalid_credentials','Adresse e-mail ou mot de passe incorrect.',401)
        with transaction.atomic():
            locked = get_user_model().objects.select_for_update().get(pk=user.pk)
            if not locked.is_active or not locked.check_password(value['password']):
                return error_response('invalid_credentials','Adresse e-mail ou mot de passe incorrect.',401)
            # Use the underlying HttpRequest; DRF's anonymous request.user is not session state.
            login(request._request, locked, backend=user.backend)
            request._request.session.set_expiry(timezone.now()+timedelta(seconds=settings.SESSION_COOKIE_AGE))
            request._request.session.save()
            AuthSession.objects.update_or_create(session_id=request._request.session.session_key, defaults={'user':locked})
        return Response(serialize_session(request._request))


class LogoutView(AuthView):
    def post(self, request):
        logout(request._request)
        return Response({'message':'Vous êtes déconnecté.'})


class MeView(AuthView):
    def get(self, request):
        underlying = request._request
        if not underlying.user.is_authenticated:
            return error_response('authentication_required','Connectez-vous pour accéder à cet espace.',401)
        return Response(serialize_session(underlying))


class PasswordResetView(AuthView):
    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        limit_request(request, 'reset', email)
        user = get_user_model().objects.filter(email__iexact=email,is_active=True).first()
        if user and user.has_usable_password():
            fragment = urlencode({'uid':urlsafe_base64_encode(force_bytes(user.pk)), 'token':default_token_generator.make_token(user)})
            # A fragment never reaches Next/HTTP access logs. Never log this URL.
            url = settings.STUDIO_ORIGIN+'/reset-password#'+fragment
            try:
                send_mail('Réinitialiser votre mot de passe — Portfolio Studio',
                          'Une réinitialisation a été demandée.\n\n'+url+'\n\nCe lien est temporaire et à usage unique. Si vous n’êtes pas à l’origine de la demande, ignorez ce message.',
                          settings.DEFAULT_FROM_EMAIL,[user.email],fail_silently=False)
            except Exception:
                logger.warning('Password reset delivery failed; recipient and link omitted.')
        return Response({'message':RESET_MESSAGE})


class PasswordResetConfirmView(AuthView):
    def post(self, request):
        limit_request(request, 'confirm')
        # Validate link syntax before password rules, without revealing an identity.
        if not isinstance(request.data, dict):
            return error_response('invalid_reset', INVALID_RESET)
        uid, token = request.data.get('uid'), request.data.get('token')
        if not isinstance(uid,str) or len(uid)>100 or not isinstance(token,str) or len(token)>200:
            return error_response('invalid_reset', INVALID_RESET)
        try:
            identity = uuid.UUID(urlsafe_base64_decode(uid).decode())
        except (ValueError, UnicodeDecodeError, TypeError):
            return error_response('invalid_reset', INVALID_RESET)
        with transaction.atomic():
            user = get_user_model().objects.select_for_update().filter(pk=identity,is_active=True).first()
            if not user or not default_token_generator.check_token(user,token):
                return error_response('invalid_reset', INVALID_RESET)
            serializer = ResetConfirmSerializer(data=request.data, context={'user':user})
            serializer.is_valid(raise_exception=True)
            user.set_password(serializer.validated_data['password'])
            user.save(update_fields=['password'])
            keys = list(AuthSession.objects.filter(user=user).values_list('session_id',flat=True))
            Session.objects.filter(session_key__in=keys).delete()
        logout(request._request)
        return Response({'message':'Mot de passe modifié. Connectez-vous avec votre nouveau mot de passe.'})
