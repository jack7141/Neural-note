from django.db import models

from knowledgesnode.models import Concept


# Create your models here.
class Connection(models.Model):
    """개념 간 연결"""
    source = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name='outgoing')
    target = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name='incoming')
    strength = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        indexes = [
            models.Index(fields=['source', 'strength']),
            models.Index(fields=['target', 'strength']),
        ]