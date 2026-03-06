import phonenumbers
from stdnum import iban


def is_valid_phone_number(value):
    try:
        phone = phonenumbers.parse(value, None)
        if not phonenumbers.is_valid_number(phone):
            return False
    except phonenumbers.NumberParseException:
        return False

    return True


def is_valid_coordinates(latitude, longitude):
    # ✅ Step 1: Ensure lat & lng are provided
    if latitude is None or longitude is None:
        return False

    try:
        # ✅ Step 2: Convert to float
        latitude = float(latitude)
        longitude = float(longitude)
    except ValueError:
        return False

    # ✅ Step 3: Ensure values are within valid ranges
    if not (-90 <= latitude <= 90):
        return False

    if not (-180 <= longitude <= 180):
        return False

    return True


def validate_iban_based_on_country(iban_number, country):
    if len(iban_number) < 2:
        return False

    try:
        iban.validate(iban_number)
        if country != iban_number[:2]:
            return False
    except Exception:
        return False
    return True
