"""
Middleware that allows a local marketplace backend to trust tokens issued by the
remote staging environment.

When `MARKETPLACE_STAGING_AUTH['ENABLED']` is set to True the middleware will:

1. Inspect every incoming request for an ``Authorization`` header.
2. Call the configured ``VERIFY_URL`` in the staging API to validate the token.
3. If the token is valid, fetch (or create) a local user that matches the
   staging response and attach it to ``request.user`` so the rest of the stack
   can treat the request as authenticated.

This is extremely useful during mobile development: developers can login
against the shared staging API and still hit their local Django server without
having to set up a dedicated authentication provider locally. In production the
flag must remain disabled.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request

from django.conf import settings
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)


@dataclass
class StagingAuthConfig:
    enabled: bool = False
    verify_url: str = ''
    timeout: int = 5
    email_field: str = 'email'

    @classmethod
    def from_settings(cls) -> 'StagingAuthConfig':
        data = getattr(settings, 'MARKETPLACE_STAGING_AUTH', {})
        return cls(
            enabled=data.get('ENABLED', False),
            verify_url=data.get('VERIFY_URL', ''),
            timeout=data.get('TIMEOUT', 5),
            email_field=data.get('EMAIL_FIELD', 'email'),
        )


class StagingTokenAuthMiddleware:
    """
    Lightweight authentication middleware for development purposes.

    Add ``apps.marketplace.middleware.staging_auth.StagingTokenAuthMiddleware``
    *after* Django's ``AuthenticationMiddleware`` to make sure a staging token
    is only used when the local request has not been authenticated yet.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.config = StagingAuthConfig.from_settings()

    def __call__(self, request):
        if self.config.enabled:
            self._maybe_attach_user(request)
        return self.get_response(request)

    # --------------------------------------------------------------------- #
    # Internals
    # --------------------------------------------------------------------- #
    def _maybe_attach_user(self, request):
        if request.user.is_authenticated:
            return
        if not self.config.verify_url:
            logger.debug('Staging auth is enabled but VERIFY_URL is missing.')
            return

        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return

        payload = self._validate_with_staging(auth_header)
        if not payload:
            return

        email = payload.get(self.config.email_field)
        if not email:
            logger.warning('Staging auth response does not contain email field.')
            return

        User = get_user_model()
        user, _ = User.objects.get_or_create(
            email=email,
            defaults={'username': email},
        )
        request.user = user

    def _validate_with_staging(self, authorization: str) -> dict[str, Any] | None:
        req = urllib_request.Request(
            self.config.verify_url,
            headers={'Authorization': authorization},
            method='GET',
        )
        try:
            with urllib_request.urlopen(req, timeout=self.config.timeout) as resp:
                if resp.status != 200:
                    return None
                body = resp.read().decode('utf-8')
                return json.loads(body)
        except (urllib_error.URLError, ValueError) as exc:
            logger.debug('Staging auth failed: %s', exc)
            return None
