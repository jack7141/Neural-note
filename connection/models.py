from django.db import models

from knowledgesnode.models import Concept


# Create your models here.
class ConnectionType(models.TextChoices):
    SAME_DOMAIN = 'same_domain', '동일 도메인'
    CROSS_DOMAIN = 'cross_domain', '교차 도메인'
    HIERARCHICAL = 'hierarchical', '계층 관계'  # 상위/하위 개념
    CAUSAL = 'causal', '인과 관계'  # 원인/결과
    ASSOCIATIVE = 'associative', '연관 관계'  # 일반적 연관


class Connection(models.Model):
    """개념 간 연결"""
    source = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name='outgoing')
    target = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name='incoming')
    strength = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    # 추가 필드
    connection_type = models.CharField(
        max_length=20,
        choices=ConnectionType.choices,
        default=ConnectionType.ASSOCIATIVE
    )
    description = models.TextField(blank=True)  # 연결에 대한 설명
    is_bidirectional = models.BooleanField(default=True)  # 양방향 연결인지

    class Meta:
        indexes = [
            models.Index(fields=['source', 'strength']),
            models.Index(fields=['target', 'strength']),
            models.Index(fields=['connection_type', 'strength']),  # 연결 유형 기반 검색
        ]