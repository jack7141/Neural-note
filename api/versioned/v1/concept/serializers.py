from rest_framework import serializers

from article.models import Article, ArticleConcept, ArticleEntity
from concept.models import Concept, ConceptDomain
from entity.models import Entity
from event.models import Event


class ConceptSerializer(serializers.ModelSerializer):
    """개념 시리얼라이저"""
    domain_name = serializers.CharField(source='domain.name', read_only=True)
    article_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Concept
        fields = ['id', 'name', 'description', 'confidence', 'domain', 'domain_name', 'article_count', 'created_at']
    
    def get_article_count(self, obj):
        return obj.articles.count()

class ConceptDomainSerializer(serializers.ModelSerializer):
    """개념 도메인 시리얼라이저"""
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    children_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ConceptDomain
        fields = ['id', 'name', 'description', 'parent', 'parent_name', 'children_count', 'created_at']
    
    def get_children_count(self, obj):
        return obj.children.count()

class EventSerializer(serializers.ModelSerializer):
    """이벤트 시리얼라이저"""
    domain_name = serializers.CharField(source='domain.name', read_only=True)
    article_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = ['id', 'name', 'description', 'event_date', 'event_type', 'domain', 'domain_name', 'article_count', 'created_at']
    
    def get_article_count(self, obj):
        return obj.articles.count()

class EntitySerializer(serializers.ModelSerializer):
    """엔티티 시리얼라이저"""
    article_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Entity
        fields = ['id', 'name', 'entity_type', 'description', 'article_count', 'created_at']
    
    def get_article_count(self, obj):
        return obj.articles.count()

class ArticleSerializer(serializers.ModelSerializer):
    """기사 시리얼라이저"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    concept_count = serializers.SerializerMethodField()
    entity_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = ['id', 'title', 'url', 'source', 'published_date', 'user', 'user_name', 
                 'concept_count', 'entity_count', 'processing_status', 'created_at']
        read_only_fields = ['processing_status', 'source', 'published_date']
    
    def get_concept_count(self, obj):
        return obj.concepts.count()
    
    def get_entity_count(self, obj):
        return obj.entities.count()

class ArticleDetailSerializer(ArticleSerializer):
    """기사 상세 시리얼라이저"""
    concepts = serializers.SerializerMethodField()
    entities = serializers.SerializerMethodField()
    events = serializers.SerializerMethodField()
    
    class Meta(ArticleSerializer.Meta):
        fields = ArticleSerializer.Meta.fields + ['content', 'summary', 'concepts', 'entities', 'events']
    
    def get_concepts(self, obj):
        article_concepts = ArticleConcept.objects.filter(article=obj).select_related('concept')
        return [{
            'id': ac.concept.id,
            'name': ac.concept.name,
            'description': ac.concept.description,
            'confidence': ac.confidence,
            'is_key_concept': ac.is_key_concept
        } for ac in article_concepts]
    
    def get_entities(self, obj):
        article_entities = ArticleEntity.objects.filter(article=obj).select_related('entity')
        return [{
            'id': ae.entity.id,
            'name': ae.entity.name,
            'entity_type': ae.entity.entity_type,
            'mention_count': ae.mention_count
        } for ae in article_entities]
    
    def get_events(self, obj):
        return [{
            'id': event.id,
            'name': event.name,
            'event_type': event.event_type,
            'event_date': event.event_date
        } for event in obj.events.all()] 