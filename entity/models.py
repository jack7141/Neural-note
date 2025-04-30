from django.db import models

# Create your models here.
class Entity(models.Model):
    """기사에 등장하는 주요 엔티티 (조직, 사람, 제품 등)"""
    name = models.CharField(max_length=255)
    entity_type = models.CharField(max_length=50)  # 조직, 인물, 제품, 기술 등
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.entity_type})"
    
    class Meta:
        verbose_name = '엔티티'
        verbose_name_plural = '엔티티 목록'
        unique_together = ('name', 'entity_type')