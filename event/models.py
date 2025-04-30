from django.db import models

from concept.models import ConceptDomain


# Create your models here.

class Event(models.Model):
    """기사들이 다루는 사건/이벤트"""
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    event_date = models.DateField(null=True, blank=True)
    event_type = models.CharField(max_length=100, blank=True)
    domain = models.ForeignKey(ConceptDomain, null=True, blank=True, on_delete=models.SET_NULL, related_name='events')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = '이벤트'
        verbose_name_plural = '이벤트 목록'


