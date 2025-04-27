from django.db import models

from model_utils.models import TimeStampedModel, UUIDModel


# Create your models here.
class ConnectionType(models.TextChoices):
    SAME_DOMAIN = 'same_domain', '동일 도메인'
    CROSS_DOMAIN = 'cross_domain', '교차 도메인'
    HIERARCHICAL = 'hierarchical', '계층 관계'  # 상위/하위 개념
    CAUSAL = 'causal', '인과 관계'  # 원인/결과
    ASSOCIATIVE = 'associative', '연관 관계'  # 일반적 연관


class Connection(UUIDModel, TimeStampedModel):
    """
    연결 - 개념들 간의 관계
    """
    source = models.ForeignKey('concept.Concept', on_delete=models.CASCADE, related_name='outgoing_connections',verbose_name='출발 개념')
    target = models.ForeignKey('concept.Concept', on_delete=models.CASCADE, related_name='incoming_connections', verbose_name='도착 개념',)
    strength = models.FloatField(default=0.0, verbose_name='연결 강도', help_text='0.0~1.0 사이의 값으로 연결 강도 표현')
    relation_type = models.CharField(max_length=50, verbose_name='관계 유형', blank=True, help_text='is_a, part_of, related_to 등')
    is_manual = models.BooleanField(default=False, verbose_name='수동 생성 여부', help_text='사용자가 직접 추가한 연결인지 여부',)

    class Meta:
        db_table = 'connections'
        verbose_name = '개념 연결'
        verbose_name_plural = '개념 연결'
        ordering = ['-strength']
        indexes = [
            models.Index(fields=['source', 'target']),
            models.Index(fields=['strength']),
        ]
    def __str__(self):
        return f'{self.source.name} -> {self.target.name} ({self.strength:.2f})'