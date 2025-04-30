from rest_framework import serializers


class CaptureSerializer(serializers.Serializer):
    """웹 페이지 캡처 시리얼라이저"""
    url = serializers.URLField(required=True)
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        default=list
    )