import pytest
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status

from accounts.models import User


@pytest.mark.django_db
def test_login_success(client, user, mocker):
    mocker.patch('accounts.modules.auth.tasks.create_user_device_task.delay', return_value=None)

    url = reverse('v1.login')
    response = client.post(url, {'email': user.email, 'password': 'password123', 'device_id': 'device_id'})
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_login_success_with_device_id(client, user, mocker):
    create_device_mock = mocker.patch('accounts.modules.auth.tasks.create_user_device_task.delay', return_value=None)

    url = reverse('v1.login')
    response = client.post(url, {'email': user.email, 'password': 'password123', 'device_id': 'device_id'})

    create_device_mock.assert_called_once_with(user.id, 'device_id')
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_login_invalid_credentials(client):
    url = reverse('v1.login')
    response = client.post(url, {'email': 'wrong@example.com', 'password': 'wrongpassword'})
    data = response.json()

    assert data['error_code'] == 'INVALID_CREDENTIALS'
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_login_inactive_user(client, inactive_user):
    url = reverse('v1.login')
    response = client.post(url, {'email': inactive_user.email, 'password': 'password123'})
    data = response.json()

    assert data['error_code'] == 'INACTIVE_ACCOUNT'
    assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.django_db
def test_signup_success(client, mocker):
    create_device_mock = mocker.patch('accounts.modules.auth.tasks.create_user_device_task.delay', return_value=None)
    send_account_verification_code_mock = mocker.patch(
        'accounts.modules.auth.tasks.send_account_verification_code_email_task.delay', return_value=None
    )

    url = reverse('v1.signup')
    response = client.post(url, {'email': 'newuser@example.com', 'password': 'password123', 'device_id': 'device_id'})

    user_created = User.objects.filter(email='newuser@example.com').last()
    create_device_mock.assert_called_once_with(user_created.id, 'device_id')
    send_account_verification_code_mock.assert_called_once_with(user_created.id)

    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_signup_success_with_preferences(client, mocker):
    create_device_mock = mocker.patch('accounts.modules.auth.tasks.create_user_device_task.delay', return_value=None)
    send_account_verification_code_mock = mocker.patch(
        'accounts.modules.auth.tasks.send_account_verification_code_email_task.delay', return_value=None
    )

    url = reverse('v1.signup')
    response = client.post(url, {'email': 'newuser@example.com', 'password': 'password123', 'device_id': 'device_id'})

    user_created = User.objects.filter(email='newuser@example.com').last()
    create_device_mock.assert_called_once_with(user_created.id, 'device_id')
    send_account_verification_code_mock.assert_called_once_with(user_created.id)

    assert user_created.user_preferences.email
    assert user_created.user_preferences.push

    assert user_created.user_preferences.available_spaces
    assert user_created.user_preferences.radar_alert
    assert user_created.user_preferences.camera_alert
    assert user_created.user_preferences.prohibited_zone_alert
    assert user_created.user_preferences.speed_limit_alert
    assert user_created.user_preferences.fatigue_alert
    assert user_created.user_preferences.police_alert
    assert user_created.user_preferences.accident_alert
    assert user_created.user_preferences.road_closed_alert

    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_signup_existing_email(client, user, mocker):
    mocker.patch('accounts.modules.auth.tasks.send_account_verification_code_email_task.delay', return_value=None)

    url = reverse('v1.signup')
    response = client.post(url, {'email': user.email, 'password': 'password123'})
    data = response.json()
    assert data['error_code'] == 'EMAIL_ALREADY_EXISTS'
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_social_login_success(client, social_user, mocker):
    mocker.patch('accounts.backends.firebase.verify_firebase_token', return_value=social_user.social_id)
    mocker.patch('accounts.modules.auth.tasks.create_user_device_task.delay', return_value=None)

    url = reverse('v1.social-login')
    response = client.post(url, {'token': 'token', 'device_id': 'device_id'})
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_social_login_invalid_credentials(client, social_user, mocker):
    mocker.patch('accounts.backends.firebase.verify_firebase_token', return_value='not_valid_social_id')
    mocker.patch('accounts.modules.auth.tasks.create_user_device_task.delay', return_value=None)

    url = reverse('v1.social-login')
    response = client.post(url, {'token': 'token', 'device_id': 'device_id'})
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_social_signup_success(client, mocker):
    class UserFirebase:
        uid = 'user_uid'
        email = 'socialnew@example.com'
        display_name = 'display_name'

    mocker.patch('accounts.modules.auth.tasks.create_user_device_task.delay', return_value=None)
    mocker.patch('accounts.backends.firebase.get_firebase_user', return_value=UserFirebase)

    url = reverse('v1.social-signup')
    response = client.post(url, {'token': 'valid_token', 'device_id': 'device_id'})
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_account_verification_success(client, inactive_user, mocker):
    hash_otp_mocker = mocker.patch('accounts.modules.auth.v1.serializers.hash_otp', return_value='hashed_otp')
    cache.set(f'account_verification__{inactive_user.uuid.hex}', 'hashed_otp', timeout=300)

    url = reverse('v1.account-verification-validate')
    response = client.post(url, {'email': inactive_user.email, 'otp': '123456'})
    hash_otp_mocker.assert_called_once_with('123456')
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_password_reset_request_success(client, user, mocker):
    verification_code_task = mocker.patch(
        'accounts.modules.auth.tasks.send_email_verification_code_task.delay', return_value=None
    )

    url = reverse('v1.password-reset-request')
    response = client.post(url, {'email': user.email})

    verification_code_task.assert_called_once_with(user.id)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_password_reset_validate_otp(client, user, mocker):
    mocker.patch('accounts.modules.auth.v1.serializers.hash_otp', return_value='hashed_otp')
    user.reset_password_requests.create(otp_hashed='hashed_otp')

    url = reverse('v1.password-reset-validate')
    response = client.post(url, {'email': user.email, 'otp': '123456'})

    assert user.reset_password_requests.is_validated()
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_password_reset_success(client, user):
    user.set_password('oldpassword')
    user.save()
    user.reset_password_requests.create(otp_hashed='hashed_otp', is_validated=True)

    url = reverse('v1.password-reset')
    response = client.post(url, {'email': user.email, 'password': 'newpassword123'})
    assert response.status_code == status.HTTP_200_OK
