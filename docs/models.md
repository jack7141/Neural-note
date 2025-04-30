# 뉴럴메모 모델 설계 문서

이 문서는 뉴럴메모 애플리케이션의 데이터 모델 구조를 자세히 설명합니다.

## 개요

뉴럴메모는 사용자의 지식을 구조화하고 연결하기 위해 다음과 같은 주요 모델을 사용합니다:

1. **Content**: 원본 콘텐츠 (웹 페이지, 문서 등)
2. **Concept**: 콘텐츠에서 추출된 핵심 개념
3. **Connection**: 개념 간의 관계
4. **Tag**: 콘텐츠와 개념을 분류하는 태그
5. **Insight**: 여러 개념에서 도출된 통찰력
6. **Review**: 개념 복습 기록

## 데이터베이스 스키마

### Content (원본 콘텐츠)

```python
class Content(models.Model):
    """사용자가 캡처한 원본 콘텐츠"""
    
    # 기본 정보
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contents')
    title = models.CharField(max_length=200)
    body = models.TextField()
    summary = models.TextField(blank=True)
    
    # 메타데이터
    source_url = models.URLField(blank=True, null=True)
    source_type = models.CharField(max_length=50)  # 'web', 'pdf', 'text', 'image' 등
    metadata = models.JSONField(default=dict, blank=True)  # 추가 메타데이터 (저자, 날짜 등)
    
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
    
    # 사용자 상호작용
    is_favorite = models.BooleanField(default=False)
    read_count = models.PositiveIntegerField(default=0)
    importance_score = models.FloatField(default=0.0)  # 알고리즘으로 계산된 중요도
    
    # 시간 정보
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_accessed_at = models.DateTimeField(null=True, blank=True)
    
    # 태그 (다대다 관계)
    tags = models.ManyToManyField('Tag', blank=True, related_name='contents')
    
    # 커스텀 매니저
    objects = models.Manager()  # 기본 매니저
    recent = RecentContentManager()  # 최근 콘텐츠 관련 쿼리 매니저
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['source_type']),
            models.Index(fields=['processing_status']),
        ]
        verbose_name = '콘텐츠'
        verbose_name_plural = '콘텐츠 목록'
    
    def __str__(self):
        return self.title
    
    # 비즈니스 로직 메서드
    def extract_concepts(self):
        """콘텐츠에서 개념을 추출하는 메서드"""
        from utils.concept_extraction import extract_concepts_from_text
        
        # 처리 중으로 상태 변경
        self.processing_status = 'processing'
        self.save(update_fields=['processing_status'])
        
        try:
            # 텍스트에서 개념 추출
            concepts_data = extract_concepts_from_text(self.body)
            
            # 추출된 개념 저장
            saved_concepts = []
            for concept_info in concepts_data:
                concept = Concept.objects.create(
                    content=self,
                    name=concept_info['name'],
                    description=concept_info.get('description', ''),
                    confidence=concept_info.get('confidence', 0.5)
                )
                
                # 벡터 임베딩 생성
                concept.generate_embedding()
                saved_concepts.append(concept)
            
            # 처리 완료로 상태 변경
            self.processing_status = 'completed'
            self.save(update_fields=['processing_status'])
            
            return saved_concepts
            
        except Exception as e:
            # 오류 발생 시 상태 업데이트
            self.processing_status = 'failed'
            self.error_message = str(e)
            self.save(update_fields=['processing_status', 'error_