import calendar
from datetime import datetime

from django.utils import timezone
from rest_framework import serializers


class YearMonthField(serializers.DateField):
    def to_internal_value(self, data):
        try:
            # First try YYYY/MM
            date = datetime.strptime(data, '%Y/%m')
        except ValueError:
            raise serializers.ValidationError("Date format must be 'YYYY/MM'.")

        # Set date to last day of the month
        last_day = calendar.monthrange(date.year, date.month)[1]
        date = datetime(date.year, date.month, last_day).date()
        today = timezone.now().date()
        if date < today:
            raise serializers.ValidationError('This card expiration date is not valid')
        return date

    def to_representation(self, value: datetime.date):
        if not value:
            return

        return {
            'month': value.month,
            'year': value.year,
        }
