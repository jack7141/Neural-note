from rest_framework import serializers


class CaptureSerializer(serializers.Serializer):
    url = serializers.CharField()