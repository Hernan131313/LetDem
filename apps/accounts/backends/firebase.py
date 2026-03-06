import firebase_admin
from django.conf import settings
from firebase_admin import auth, credentials


def initialize_firebase():
    if settings.LOCAL or settings.TEST:
        return

    try:
        # Initialize Firebase Admin SDK
        firebase_credentials = credentials.Certificate(settings.FIREBASE_SERVICE_CONFIG)
        if not firebase_admin._apps:  # Ensure Firebase is initialized only once
            firebase_admin.initialize_app(firebase_credentials)

    except Exception as e:
        raise Exception(f'Error initializing Firebase Admin: {str(e)}')


def verify_firebase_token(token: str):
    if settings.LOCAL or settings.TEST:
        return

    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token['uid']  # The user's unique Firebase UID
    except Exception:
        return None


def get_firebase_user(token: str):
    if settings.LOCAL or settings.TEST:
        return

    try:
        # Fetch user details from Firebase
        social_id = verify_firebase_token(token)
        if not social_id:
            return

        user = auth.get_user(social_id)
        return user
    except Exception:
        return None
