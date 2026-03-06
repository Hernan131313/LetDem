from commons.exceptions.types import accounts as accounts_exceptions
from commons.paginators import CustomPagination
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Contribution, Notification, ScheduledNotification
from accounts.modules.users.v1 import serializers


class UserMeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        serializer = serializers.UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        user = request.user
        serializer = serializers.UpdateUserInfoSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_user = serializer.save()
        return Response(serializers.UserSerializer(updated_user).data, status=status.HTTP_200_OK)


class ChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        user = request.user
        serializer = serializers.ChangePasswordSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data={'message': 'Password changed successfully'}, status=status.HTTP_200_OK)


class DeleteAccountAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        user = request.user
        user.delete()
        return Response(data={'message': 'Account deleted successfully'}, status=status.HTTP_200_OK)


class CarAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        if not getattr(user, 'car', None):
            raise accounts_exceptions.UserDoesNotHaveCar()

        serializer = serializers.CarSerializer(user.car, context={'user': user})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = serializers.CreateCarSerializer(data=request.data, context={'user': user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, *args, **kwargs):
        user = request.user
        serializer = serializers.UpdateCarSerializer(user.car, data=request.data, context={'user': user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class CarParkedPlaceAddressAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        user = request.user
        serializer = serializers.CarParkedPlaceAddressSerializer(user.car, data=request.data, context={'user': user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class HomeAddressAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = serializers.AddHomeAddressSerializer(data=request.data, context={'user': user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        user = request.user
        user.addresses.home().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class WorkAddressAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = serializers.AddWorkAddressSerializer(data=request.data, context={'user': user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        user = request.user
        user.addresses.work().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoritesAddressAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        addresses = []

        if hasattr(user, 'addresses'):
            addresses = user.addresses.all()

        serializer = serializers.FavoriteAddressSerializer(addresses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ContributionsListAPIView(APIView):
    """
    API View to list contributions, filtered by query parameters:
    - `?type=SPACE` → Returns only SPACE contributions
    - `?type=EVENT` → Returns only EVENT contributions
    """

    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get(self, request, *args, **kwargs):
        user = request.user
        queryset = getattr(user, 'contributions', Contribution.objects.none()).all()

        # Filter by type (SPACE or EVENT)
        contribution_type = request.query_params.get('type', None)
        if contribution_type == Contribution.Type.SPACE:
            queryset = queryset.spaces()
        elif contribution_type == Contribution.Type.EVENT:
            queryset = queryset.events()

        # Paginate the queryset
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(queryset, request)

        # Serialize the data
        serializer = serializers.ContributionSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)


class ScheduledNotificationAPIView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    serializer_class = serializers.ScheduledNotificationSerializer

    def get(self, request, *args, **kwargs):
        """
        API View to list scheduled notifications by the user
        - `?page=1` → Page number
        - `?page_size=15` → List of items per page
        """

        user = request.user
        queryset = getattr(user, 'scheduled_notifications', ScheduledNotification.objects.none()).all()

        # Paginate the queryset
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(queryset, request)

        # Serialize the data
        serializer = self.serializer_class(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = serializers.CreateScheduledNotificationSerializer(data=request.data, context={'user': user})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        serialized_data = self.serializer_class(instance).data
        return Response(data=serialized_data, status=status.HTTP_201_CREATED)

    def put(self, request, uuid, *args, **kwargs):
        user = request.user
        queryset = getattr(user, 'scheduled_notifications', ScheduledNotification.objects.none())
        instance = queryset.filter(uuid=uuid).last()
        if not instance:
            return Response(data={'error': 'Item not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = serializers.ReScheduledNotificationSerializer(instance=instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        serialized_data = self.serializer_class(instance).data
        return Response(data=serialized_data, status=status.HTTP_201_CREATED)

    def delete(self, request, uuid, *args, **kwargs):
        user = request.user
        queryset = getattr(user, 'scheduled_notifications', ScheduledNotification.objects.none())
        instance = queryset.filter(uuid=uuid).last()
        if not instance:
            return Response(data={'error': 'Item not found.'}, status=status.HTTP_404_NOT_FOUND)

        instance.delete()
        return Response(data={'message': 'Scheduled Notification Deleted'}, status=status.HTTP_204_NO_CONTENT)


class UserPreferencesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        user = request.user
        serializer = serializers.UpdateUserPreferences(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data={'message': 'User Preferences Updated'}, status=status.HTTP_200_OK)


class NotificationsListDeleteAllAPIView(APIView):
    """
    API View to list notifications, and delete all filtered by query parameters:
    - `?read=false` → Returns only not read notifications
    """

    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get(self, request, *args, **kwargs):
        user = request.user
        queryset = getattr(user, 'notifications', Notification.objects.none()).all()

        notification_read = request.query_params.get('read', None)
        if notification_read in ['false', 'False']:
            queryset = queryset.unread()
        elif notification_read is True:
            queryset = queryset.read()

        # Paginate the queryset
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(queryset, request)

        # Serialize the data
        serializer = serializers.NotificationSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)

    def delete(self, request, *args, **kwargs):
        user = request.user
        queryset = getattr(user, 'notifications', Notification.objects.none())
        queryset.all().delete()
        return Response(data={'message': 'Notifications deleted'}, status=status.HTTP_200_OK)


class NotificationReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, uuid, *args, **kwargs):
        user = request.user
        queryset = getattr(user, 'notifications', Notification.objects.none())
        instance = queryset.filter(uuid=uuid).last()
        if not instance:
            return Response(data={'error': 'Notification not found.'}, status=status.HTTP_404_NOT_FOUND)

        instance.read = True
        instance.save()
        return Response(data={'message': 'Notification read'}, status=status.HTTP_200_OK)


class ChangeUserLanguageAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        user = request.user
        serializer = serializers.ChangeUserLanguageSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data={'message': 'User language changed successfully'}, status=status.HTTP_200_OK)


class UpdateDeviceIdAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        user = request.user
        serializer = serializers.UpdateDeviceIdSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data={'message': 'Device Id updated successfully'}, status=status.HTTP_200_OK)
