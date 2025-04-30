from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class ConceptDomain(models.Model):
    """개념 도메인 (분야/카테고리)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = '개념 도메인'
        verbose_name_plural = '개념 도메인 목록'

class Concept(models.Model):
    """기사에서 추출된 핵심 아이디어나 주제"""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    confidence = models.FloatField(default=0.0)  # 개념 추출 확신도
    domain = models.ForeignKey(ConceptDomain, null=True, blank=True, on_delete=models.SET_NULL, related_name='concepts')
    embedding = models.JSONField(null=True, blank=True)  # 벡터 임베딩 저장
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = '개념'
        verbose_name_plural = '개념 목록'
        unique_together = ('name', 'domain')
    
    def generate_embedding(self):
        """개념에 대한 벡터 임베딩 생성"""
        # 임베딩 생성 로직 구현
        # TODO: 실제 임베딩 생성 로직 구현
        pass


class ConceptRelationship(models.Model):
    """개념 간의 관계"""
    source_concept = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name='source_relationships')
    target_concept = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name='target_relationships')
    relationship_type = models.CharField(max_length=50)  # IS_A, PART_OF, RELATED_TO, etc.
    weight = models.FloatField(default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.source_concept.name} -> {self.relationship_type} -> {self.target_concept.name}"
    
    class Meta:
        unique_together = ('source_concept', 'target_concept', 'relationship_type')