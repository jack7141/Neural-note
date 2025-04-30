# 뉴럴메모 시스템 아키텍처

이 문서는 뉴럴메모의 시스템 아키텍처와 Django에서의 구현 방법에 대해 설명합니다.

## 아키텍처 개요

뉴럴메모는 다음과 같은 계층으로 구성됩니다:

```
+-----------------------+
|      프론트엔드        |
| (React Native 모바일 앱) |
+-----------------------+
           |
           v
+-----------------------+
|       API 계층         |
| (Django REST Framework) |
+-----------------------+
           |
           v
+-----------------------+
|     비즈니스 로직 계층   |
|  (Django 모델 & 매니저)  |
+-----------------------+
           |
           v
+-----------------------+
|    데이터 접근 계층     |
|    (Django ORM)       |
+-----------------------+
           |
           v
+-----------------------+
|     데이터베이스        |
| (SQLite/PostgreSQL)   |
+-----------------------+
```

## Fat Model, Thin View 패턴

뉴럴메모는 Django의 "Fat Model, Thin View" 패턴을 따릅니다. 이 접근법에서는:

1. **모델(Fat)**: 비즈니스 로직의 대부분을 포함
2. **뷰(Thin)**: 요청 처리 및 응답 반환만 담당
3. **시리얼라이저**: 복잡한 데이터 변환 로직을 처리

### 비즈니스 로직 구현 방식

1. **모델 메서드**: 단일 모델 인스턴스와 관련된 로직
2. **모델 매니저**: 모델 컬렉션 전체에 대한 작업 (쿼리셋 조작 등)
3. **모델 시그널**: 모델 이벤트에 반응하는 로직 (저장 전/후 처리 등)
4. **시리얼라이저 메서드**: 데이터 변환 및 유효성 검사 로직

### 서비스 레이어 사용 지양

일반적인 서비스 레이어 대신, 다음 방식을 활용합니다:

1. **커스텀 모델 매니저**: 복잡한 쿼리 로직 캡슐화
2. **모델 인스턴스 메서드**: 비즈니스 로직 캡슐화
3. **비동기 태스크**: 오래 걸리는 작업을 비동기적으로 처리 (Celery 활용)

## 각 계층별 상세 설명

### 1. 프론트엔드 계층 (React Native)

- 모바일 사용자 인터페이스
- 상태 관리
- API 호출 및 데이터 표시
- 로컬 캐싱
- 오프라인 지원

### 2. API 계층 (Django REST Framework)

- 인증 및 권한 관리
- 요청 검증
- 시리얼라이저를 통한 데이터 변환
- 페이징, 필터링, 검색 처리
- API 버전 관리

### 3. 비즈니스 로직 계층 (Django 모델 & 매니저)

- 데이터 유효성 검사
- 비즈니스 규칙 적용
- AI 모델 통합
- 벡터 임베딩 생성 및 처리
- 개념 간 연결 관리
- 인사이트 생성

### 4. 데이터 접근 계층 (Django ORM)

- 데이터베이스 쿼리 생성
- 트랜잭션 관리
- 인덱스 활용
- 쿼리 최적화

### 5. 데이터베이스 계층 (SQLite/PostgreSQL)

- 개발: SQLite
- 배포: PostgreSQL
- 벡터 저장 기능 활용
- 인덱싱 전략

## Django 구현 패턴

### 모델 구현 패턴

```python
class Content(models.Model):
    # 필드 정의
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    # ... 기타 필드
    
    # 커스텀 매니저
    objects = models.Manager()  # 기본 매니저
    recent = RecentContentManager()  # 최근 콘텐츠 관련 쿼리 전문 매니저
    
    # 인스턴스 메서드 (비즈니스 로직)
    def extract_concepts(self):
        """콘텐츠에서 개념 추출"""
        # 개념 추출 로직
        return concept_list
    
    def get_related_content(self, limit=5):
        """관련 콘텐츠 찾기"""
        # 관련 콘텐츠 검색 로직
        return related_content_list
    
    # 속성 메서드
    @property
    def word_count(self):
        """콘텐츠 단어 수 계산"""
        return len(self.body.split())
    
    # 메타 정보
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['source_type']),
        ]
```

### 커스텀 모델 매니저 패턴

```python
class RecentContentManager(models.Manager):
    def get_queryset(self):
        """기본 쿼리셋을 최근 콘텐츠로 필터링"""
        return super().get_queryset().filter(
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        )
    
    def with_concepts_count(self):
        """개념 수를 포함한 쿼리셋 반환"""
        return self.get_queryset().annotate(
            concepts_count=models.Count('concepts')
        )
    
    def by_source_type(self, source_type):
        """특정 소스 타입의 콘텐츠만 필터링"""
        return self.get_queryset().filter(source_type=source_type)
```

### 시리얼라이저 구현 패턴

```python
class ContentSerializer(serializers.ModelSerializer):
    concepts_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Content
        fields = ['id', 'title', 'body', 'source_url', 'source_type', 
                  'created_at', 'concepts_count']
    
    def create(self, validated_data):
        """콘텐츠 생성 및 개념 추출 처리"""
        content = Content.objects.create(**validated_data)
        
        # 비동기 태스크로 개념 추출 요청
        from .tasks import extract_concepts_task
        extract_concepts_task.delay(content.id)
        
        return content
    
    def to_representation(self, instance):
        """응답 데이터 커스터마이징"""
        data = super().to_representation(instance)
        
        # 요청에 따라 본문 길이 제한
        request = self.context.get('request')
        if request and request.query_params.get('summary') == 'true':
            data['body'] = instance.body[:200] + '...' if len(instance.body) > 200 else instance.body
        
        return data
```

### 뷰셋 구현 패턴

```python
class ContentViewSet(viewsets.ModelViewSet):
    serializer_class = ContentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['source_type']
    search_fields = ['title', 'body']
    ordering_fields = ['created_at', 'title']
    
    def get_queryset(self):
        """현재 사용자의 콘텐츠만 필터링"""
        return Content.objects.filter(user=self.request.user).annotate(
            concepts_count=models.Count('concepts')
        )
    
    def perform_create(self, serializer):
        """생성 시 현재 사용자 할당"""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def extract_concepts(self, request, pk=None):
        """수동 개념 추출 액션"""
        content = self.get_object()
        concepts = content.extract_concepts()
        
        return Response({
            'message': f'{len(concepts)} concepts extracted successfully',
            'concepts': ConceptSerializer(concepts, many=True).data
        })
```

### 비동기 태스크 패턴 (Celery)

```python
@shared_task
def extract_concepts_task(content_id):
    """콘텐츠에서 개념을 추출하는 비동기 태스크"""
    try:
        content = Content.objects.get(id=content_id)
        concepts = content.extract_concepts()
        
        # 개념 저장 후 연결 만들기
        for concept in concepts:
            find_and_create_connections(concept)
            
        return f"Successfully extracted {len(concepts)} concepts"
    except Content.DoesNotExist:
        return "Content not found"
    except Exception as e:
        return f"Error during concept extraction: {str(e)}"
```

## 주요 모듈 간 상호작용

### 콘텐츠 캡처 및 개념 추출 흐름

1. 사용자가 API를 통해 콘텐츠 URL 제출
2. View에서 URL 유효성 검사 및 콘텐츠 생성
3. 비동기 태스크로 콘텐츠 본문 추출 및 개념 추출 요청
4. 콘텐츠 모델의 메서드를 통해 개념 추출 및 저장
5. 새 개념들에 대해 벡터 임베딩 생성
6. 기존 개념들과의 유사도 계산 및 연결 생성
7. 사용자에게 처리 완료 알림

### 지식 그래프 조회 흐름

1. 사용자가 개념 ID 또는 전체 그래프 요청
2. View에서 요청 파라미터 검증
3. 커스텀 매니저 메서드를 통해 그래프 데이터 구성
4. 노드(개념)와 엣지(연결) 정보 포함한 응답 반환
5. 프론트엔드에서 그래프 시각화

## 비즈니스 로직 구현 위치

### 모델에 구현할 로직

- 개념 추출 알고리즘
- 벡터 임베딩 생성
- 유사도 계산
- 복습 시점 계산
- 중요도 평가

### 시리얼라이저에 구현할 로직

- 데이터 변환 및 포맷팅
- 복잡한 유효성 검사
- 중첩 객체 처리
- 데이터 필터링 및 마스킹

### 뷰에 구현할 로직

- 인증 및 권한 검사
- 요청 파라미터 검증
- 응답 포맷 결정
- HTTP 상태 코드 처리

## 성능 최적화 전략

### 쿼리 최적화

- `select_related`와 `prefetch_related` 적극 활용
- 필요한 필드만 `only()` 또는 `defer()` 활용
- 데이터베이스 인덱스 전략적 활용
- 쿼리 캐싱 활용

### 벡터 연산 최적화

- 벡터 연산을 데이터베이스 내에서 처리 (PostgreSQL 벡터 확장 활용)
- 배치 처리로 여러 벡터 연산 한 번에 수행
- 필요한 경우 근사 검색 알고리즘 활용

### 캐싱 전략

- Redis를 활용한 자주 접근하는 데이터 캐싱
- 그래프 데이터 캐싱
- 사용자별 인사이트 캐싱
- 시간 기반 캐시 무효화

## 확장성 고려사항

### 데이터베이스 확장

- 초기: SQLite로 개발 및 테스트
- 베타 단계: PostgreSQL로 마이그레이션
- 확장 단계: 필요시 그래프 데이터베이스 통합 검토 (Neo4j 등)

### 장기적 고려사항

- 마이크로서비스 분리 가능성 검토
  - AI 처리 서비스
  - 그래프 쿼리 서비스
  - 사용자 데이터 서비스
- 컨테이너화 및 오케스트레이션 (Docker, Kubernetes)
- API 게이트웨이 도입

이 아키텍처는 프로젝트의 성장에 따라 지속적으로 발전할 예정입니다. 현재 POC 단계에서는 모놀리식 Django 애플리케이션으로 시작하여 검증 후 필요에 따라 아키텍처를 확장해 나갈 계획입니다.

## 주요 AI 통합 지점

### 1. 개념 추출 (LLM 활용)

```python
def extract_concepts_from_text(text, max_concepts=5):
    """텍스트에서 LLM을 사용하여 핵심 개념을 추출"""
    
    prompt = f"""
    다음 텍스트에서 가장 중요한 개념, 주제, 키워드를 추출해주세요.
    각 개념에 대해 다음 정보를 제공해주세요:
    1. 개념 이름 (짧은 구문)
    2. 간략한 설명
    3. 신뢰도 점수 (0-1 사이, 이 개념이 텍스트에서 얼마나 명확하게 등장하는지)
    
    JSON 형식으로 응답해주세요.
    최대 {max_concepts}개의 개념만 추출해주세요.
    
    텍스트:
    {text}
    """
    
    # OpenAI API 호출
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "너는 텍스트에서 핵심 개념을 추출하는 전문가입니다."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
    )
    
    # JSON 응답 파싱
    try:
        content = response.choices[0].message.content
        concepts_data = json.loads(content)
        return concepts_data
    except Exception as e:
        logger.error(f"Failed to parse LLM response: {e}")
        return []
```

### 2. 벡터 임베딩 생성

```python
def generate_concept_embedding(concept_name, concept_description):
    """개념 이름과 설명을 결합하여 벡터 임베딩 생성"""
    
    # Sentence-BERT 모델 로드
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # 텍스트 결합 및 임베딩 생성
    combined_text = f"{concept_name}: {concept_description}"
    embedding = model.encode(combined_text)
    
    # numpy 배열을 리스트로 변환 (JSON 저장용)
    return embedding.tolist()
```

### 3. 유사도 계산 및 연결 생성

```python
def find_similar_concepts(concept, threshold=0.8, limit=10):
    """개념과 유사한 다른 개념들 찾기"""
    
    # 새 개념의 임베딩
    new_embedding = np.array(concept.vector_embedding)
    
    # 기존 개념들 조회 (현재 개념 제외)
    existing_concepts = Concept.objects.exclude(id=concept.id).filter(
        content__user=concept.content.user
    )
    
    # 각 개념과의 유사도 계산
    similarities = []
    
    for existing in existing_concepts:
        if existing.vector_embedding:
            existing_embedding = np.array(existing.vector_embedding)
            
            # 코사인 유사도 계산
            similarity = cosine_similarity(
                new_embedding.reshape(1, -1), 
                existing_embedding.reshape(1, -1)
            )[0][0]
            
            if similarity >= threshold:
                similarities.append({
                    'concept': existing,
                    'similarity': float(similarity)
                })
    
    # 유사도 순으로 정렬
    similarities.sort(key=lambda x: x['similarity'], reverse=True)
    
    # 상위 N개 반환
    return similarities[:limit]
```

### 4. 인사이트 생성

```python
def generate_insights(concepts, user):
    """여러 개념을 바탕으로 인사이트 생성"""
    
    # 개념 데이터 준비
    concept_data = []
    for concept in concepts:
        concept_data.append({
            'name': concept.name,
            'description': concept.description,
            'source': concept.content.title,
            'created_at': concept.created_at.isoformat()
        })
    
    # 연결 데이터 준비
    connection_data = []
    for i, source in enumerate(concepts):
        for j, target in enumerate(concepts):
            if i != j:
                # 두 개념 간 연결 찾기
                conn = Connection.objects.filter(
                    Q(source=source, target=target) | Q(source=target, target=source)
                ).first()
                
                if conn:
                    connection_data.append({
                        'source': source.name,
                        'target': target.name,
                        'similarity': conn.similarity
                    })
    
    # LLM 프롬프트 구성
    prompt = f"""
    다음은 사용자가 저장한 지식 조각들입니다:
    
    개념들:
    {json.dumps(concept_data, indent=2)}
    
    이 개념들 간의 연결:
    {json.dumps(connection_data, indent=2)}
    
    이 정보들을 바탕으로 다음을 생성해주세요:
    1. 통합된 인사이트 (150-200자)
    2. 발견되는 패턴이나 특이점 (최대 3개)
    3. 탐색할 만한 새로운 질문 (2개)
    4. 추천 관련 주제 (3개)
    
    JSON 형식으로 응답해주세요.
    """
    
    # OpenAI API 호출
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "너는 여러 개념과 지식을 연결하여 인사이트를 제공하는 전문가입니다."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )
    
    # 응답 처리
    content = response.choices[0].message.content
    insights_data = json.loads(content)
    
    # 인사이트 저장 및 반환
    insight = Insight.objects.create(
        user=user,
        title=f"인사이트: {', '.join([c.name for c in concepts[:2]])} 외",
        content=json.dumps(insights_data),
    )
    insight.concepts.set(concepts)
    
    return insights_data
```

## 아키텍처 보안 고려사항

### 데이터 보안

- 사용자 데이터 암호화 (저장 시)
- API 엔드포인트 HTTPS 적용
- 민감한 구성 정보 환경변수로 관리
- Django 기본 보안 설정 활성화

### 사용자 인증 및 권한

- JWT 기반 인증 시스템
- 세션 타임아웃 및 토큰 갱신 정책
- API 권한에 Django 권한 시스템 활용
- 2단계 인증 옵션 제공 (선택적)

### 개인정보 보호

- 사용자 동의에 기반한 데이터 수집
- 명확한 데이터 처리 정책
- 데이터 내보내기 및 삭제 기능 제공
- 타사 서비스 통합 시 데이터 공유 제한