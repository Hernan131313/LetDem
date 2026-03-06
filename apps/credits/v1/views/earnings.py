from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from credits.v1.serializers import earnings


class EarningAccountAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = earnings.EarningAccountSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(earnings.RetrieveEarningAccountSerializer(instance).data, status=status.HTTP_201_CREATED)


class AccountAddressAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = earnings.AccountAddressSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(
            earnings.RetrieveEarningAccountSerializer(instance.account).data, status=status.HTTP_201_CREATED
        )


class AccountIDDocumentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = earnings.AccountIDDocumentSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(
            earnings.RetrieveEarningAccountSerializer(instance.account).data, status=status.HTTP_201_CREATED
        )


class AccountBankAccountAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = earnings.CreatePayoutMethodSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(
            earnings.RetrieveEarningAccountSerializer(instance.account).data, status=status.HTTP_201_CREATED
        )
