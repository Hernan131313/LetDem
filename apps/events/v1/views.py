from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from events.v1 import serializers


class CreateEventAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = serializers.CreateEventSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Event created successfully'}, status=status.HTTP_201_CREATED)


class CreateEventFeedbackAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, uuid, *args, **kwargs):
        user = request.user
        serializer = serializers.CreateEventFeedbackSerializer(
            data=request.data, context={'event_id': uuid, 'user': user}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Event feedback created successfully'}, status=status.HTTP_201_CREATED)
