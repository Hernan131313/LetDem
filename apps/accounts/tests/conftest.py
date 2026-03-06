import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def user(db):
    """Creates and returns a test user"""
    user = User.objects.create_user(email='test@example.com', password='password123', is_active=True)
    return user


@pytest.fixture
def inactive_user(db):
    """Creates and returns a test user"""
    return User.objects.create_user(email='test@example.com', password='password123', is_active=False)


@pytest.fixture
def social_user():
    return User.objects.create_user(email='social@example.com', social_id='social_id', is_active=True)
