from typing import List

from django.db import models
from model_utils.models import TimeStampedModel, UUIDModel

from django.db.models.functions import Length

from utils.calculator import next_code


class ConceptDomainManager(models.Manager):
    def annotated_code_length(self):
        return self.get_queryset().annotate(code_len=Length('code')).order_by('code_len', 'code')

    def get_or_bulk_create(self, names: List[str]):
        exists_codes = self.get_queryset().filter(display_name__in=names)
        no_exists = [n for n in names]
        for c in exists_codes:
            name = c.display_name
            if name in names:
                no_exists.remove(name)
                pass
            pass
        last_code = ConceptDomain.objects.annotated_code_length().last().code

        codes = []
        for _ in no_exists:
            last_code = next_code(last_code)
            codes.append(last_code)
        categories = [ConceptDomain(name_of_manage=i, display_name=i, index=1, code=c,) for c, i in zip(codes, no_exists)]
        if len(categories) != 0:
            self.bulk_create(categories)
        stored = self.get_queryset().filter(display_name__in=names)
        return stored

class ConceptDomain(TimeStampedModel):
    """
    개념 도메인 - 특정 분야나 주제 영역을 정의하는 카테고리 시스템
    """
    code = models.CharField(primary_key=True, max_length=50, verbose_name='도메인 코드',)
    name = models.CharField(max_length=100, verbose_name='도메인 명칭', unique=True)
    description = models.TextField(verbose_name='설명', help_text='도메인에 대한 상세 설명', blank=True,)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children', verbose_name='상위 도메인')
    is_active = models.BooleanField(default=True, verbose_name='활성화 여부',)
    objects = ConceptDomainManager()

    class Meta:
        db_table = 'concept_domains'
        verbose_name = '개념 도메인'
        verbose_name_plural = '개념 도메인'
        ordering = ['name']

    def __str__(self):
        return f'{self.name}'

    @property
    def is_leaf(self):
        return self.children.all().count() == 0


class Concept(UUIDModel, TimeStampedModel):
    """
    개념 - 콘텐츠에서 추출된 핵심 키워드나 개념
    """
    name = models.CharField(max_length=100, verbose_name='개념명', db_index=True)
    slug = models.SlugField(max_length=150, verbose_name='슬러그', unique=True, blank=True,)
    content = models.ForeignKey('content.Content', on_delete=models.CASCADE, related_name='concepts', verbose_name='출처 콘텐츠')
    domain = models.ForeignKey(ConceptDomain, on_delete=models.SET_NULL, null=True, related_name='concepts', verbose_name='도메인',)
    confidence = models.FloatField(default=0.0, verbose_name='신뢰도', help_text='0.0~1.0 사이의 값')
    vector_embedding = models.JSONField(null=True, blank=True, verbose_name='벡터 임베딩', help_text='개념의 의미적 임베딩 벡터')
    is_reviewed = models.BooleanField(default=False, verbose_name='검토 여부')

    def __str__(self):
        return f'{self.name} ({self.confidence:.2f})'


    class Meta:
        db_table = 'concepts'
        verbose_name = '개념'
        verbose_name_plural = '개념'
        ordering = ['-confidence']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['confidence']),
        ]


class ConceptCluster(TimeStampedModel):
    """유사 개념들의 클러스터"""
    name = models.CharField(max_length=100)
    domain = models.ForeignKey(ConceptDomain, on_delete=models.CASCADE, related_name='clusters')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.domain.name})"

    class Meta:
        unique_together = ['name', 'domain']


class ConceptClusterMembership(TimeStampedModel):
    """개념과 클러스터 간의 관계"""
    concept = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name='cluster_memberships')
    cluster = models.ForeignKey(ConceptCluster, on_delete=models.CASCADE, related_name='memberships')
    relevance_score = models.FloatField(default=1.0)  # 클러스터와의 관련성 점수
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['concept', 'cluster']