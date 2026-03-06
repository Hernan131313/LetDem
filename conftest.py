import django
import pytest
from rest_framework.test import APIClient


@pytest.fixture(scope='session', autouse=True)
def setup_django():
    """Ensure Django is set up before running tests."""
    django.setup()


@pytest.fixture
def client():
    """Provides an API client for making requests."""
    return APIClient()


@pytest.fixture
def mocker(mocker):
    """Provides a mocker instance for patching dependencies."""
    return mocker
