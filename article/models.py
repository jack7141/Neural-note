from django.db import models
from django.contrib.auth import get_user_model

from concept.models import Concept, ConceptDomain
from entity.models import Entity
from event.models import Event

User = get_user_model()

class Article(models.Model):
    """사용자가 저장한 웹 기사나 문서의 원본 데이터"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='articles')
    title = models.CharField(max_length=255)
    url = models.URLField()
    content = models.TextField()
    summary = models.TextField(blank=True)
    
    # 메타데이터
    source = models.CharField(max_length=100, blank=True)  # 언론사
    published_date = models.DateField(null=True, blank=True)
    
    # 처리 상태
    processing_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', '처리 대기'),
            ('processing', '처리 중'),
            ('completed', '처리 완료'),
            ('failed', '처리 실패')
        ],
        default='pending'
    )
    error_message = models.TextField(blank=True)
    
    # 관계 필드
    concepts = models.ManyToManyField(Concept, through='ArticleConcept', related_name='articles')
    entities = models.ManyToManyField(Entity, through='ArticleEntity', related_name='articles')
    events = models.ManyToManyField(Event, through='ArticleEvent', related_name='articles')
    domains = models.ManyToManyField(ConceptDomain, related_name='articles')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = '기사'
        verbose_name_plural = '기사 목록'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['processing_status']),
        ]


class ArticleConcept(models.Model):
    """기사와 개념 간의 관계"""
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    concept = models.ForeignKey(Concept, on_delete=models.CASCADE)
    confidence = models.FloatField(default=0.0)  # 이 기사에서 해당 개념의 관련성 점수
    is_key_concept = models.BooleanField(default=False)  # 핵심 개념 여부
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.article.title} - {self.concept.name}"
    
    class Meta:
        unique_together = ('article', 'concept')



class ArticleEntity(models.Model):
    """기사와 엔티티 간의 관계"""
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    confidence = models.FloatField(default=0.0)
    mention_count = models.IntegerField(default=1)  # 기사 내 해당 엔티티 언급 횟수
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.article.title} - {self.entity.name}"
    
    class Meta:
        unique_together = ('article', 'entity')


class ArticleEvent(models.Model):
    """기사와 이벤트 간의 관계"""
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    relationship_type = models.CharField(max_length=50, default='PART_OF')  # PART_OF, MENTIONS, etc.
    confidence = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.article.title} - {self.event.name}"
    
    class Meta:
        unique_together = ('article', 'event')

class ArticleRelationship(models.Model):
    """기사 간의 관계"""
    source_article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='source_relationships')
    target_article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='target_relationships')
    relationship_type = models.CharField(max_length=50)  # RELATED_TO, CONTRADICTS, SUPPORTS, FOLLOWS, etc.
    similarity_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.source_article.title} -> {self.relationship_type} -> {self.target_article.title}"
    
    class Meta:
        unique_together = ('source_article', 'target_article', 'relationship_type')
