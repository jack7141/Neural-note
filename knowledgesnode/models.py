from django.db import models

from concept.models import ConceptDomain


# Create your models here.

class Content(models.Model):
    """사용자가 캡처한 콘텐츠 정보"""
    title = models.CharField(max_length=200)
    content = models.TextField()
    source_url = models.URLField(blank=True, null=True)
    source_type = models.CharField(max_length=50, default='web')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ContentAnalysis(models.Model):
    """콘텐츠 분석 결과"""
    content = models.OneToOneField(Content, on_delete=models.CASCADE, related_name='analysis')
    category = models.CharField(max_length=100, db_index=True)  # 인덱스 추가
    emotional_tone = models.CharField(max_length=50, db_index=True)  # 인덱스 추가
    temporal_context = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # 원본 JSON 응답 저장 (선택적)
    raw_analysis = models.JSONField(null=True, blank=True)


class CoreTheme(models.Model):
    """핵심 주제"""
    content_analysis = models.ForeignKey(ContentAnalysis, on_delete=models.CASCADE, related_name='core_themes')
    theme = models.CharField(max_length=200, db_index=True)

    class Meta:
        unique_together = ['content_analysis', 'theme']


class Concept(models.Model):
    """추출된 개념"""
    content_analysis = models.ForeignKey(ContentAnalysis, on_delete=models.CASCADE, related_name='concepts')
    name = models.CharField(max_length=100, db_index=True)
    confidence = models.FloatField()
    vector_embedding = models.JSONField(null=True, blank=True)
    category = models.CharField(max_length=100, blank=True)  # 기존 필드
    domain = models.ForeignKey(ConceptDomain, on_delete=models.SET_NULL, null=True, related_name='concepts')  # 추가
    created_at = models.DateTimeField(auto_now_add=True)

    # 개념 표현을 풍부하게 하는 필드들 추가
    definition = models.TextField(blank=True)  # 개념 정의
    importance_score = models.FloatField(default=0.0)  # 중요도 점수
    context_snippet = models.TextField(blank=True)  # 개념이 등장한 원문 일부

    class Meta:
        indexes = [
            models.Index(fields=['name', 'confidence']),
            models.Index(fields=['domain', 'importance_score']),  # 도메인 기반 검색 최적화
        ]


class KeyClaim(models.Model):
    """핵심 주장/관점"""
    content_analysis = models.ForeignKey(ContentAnalysis, on_delete=models.CASCADE, related_name='key_claims')
    claim = models.TextField()

    class Meta:
        unique_together = ['content_analysis', 'claim']


class RelatedDomain(models.Model):
    """관련 도메인"""
    content_analysis = models.ForeignKey(ContentAnalysis, on_delete=models.CASCADE, related_name='related_domains')
    domain = models.CharField(max_length=100, db_index=True)

    class Meta:
        unique_together = ['content_analysis', 'domain']


class KeyTerm(models.Model):
    """중요 용어나 전문 용어"""
    content_analysis = models.ForeignKey(ContentAnalysis, on_delete=models.CASCADE, related_name='key_terms')
    term = models.CharField(max_length=100, db_index=True)

    class Meta:
        unique_together = ['content_analysis', 'term']