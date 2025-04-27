from django.db import models
from model_utils.models import TimeStampedModel, UUIDModel

from concept.models import ConceptDomain


class Content(UUIDModel, TimeStampedModel):
    """
    컨텐츠 - 뉴스 기사, 블로그 포스트 등 텍스트 기반 콘텐츠
    """
    title = models.CharField(max_length=600, verbose_name='제목')
    content = models.TextField(verbose_name='내용')
    source_url = models.URLField(verbose_name='출처 URL', blank=True, null=True,)
    source_type = models.CharField(max_length=50, verbose_name='소스 타입', default='web', help_text='web, pdf, image, audio 등')
    primary_domain = models.ForeignKey(ConceptDomain, on_delete=models.SET_NULL, null=True, blank=True, related_name='primary_contents', verbose_name='주요 도메인')
    is_processed = models.BooleanField(default=False, verbose_name='처리 완료 여부')

    class Meta:
        db_table = 'contents'
        verbose_name = '컨텐츠'
        verbose_name_plural = '컨텐츠'
        ordering = ['-created']

    def __str__(self):
        return f'{self.title}'