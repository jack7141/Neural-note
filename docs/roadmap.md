# 뉴럴메모 개발 로드맵

이 문서는 뉴럴메모 프로젝트의 개발 계획과 향후 기능 구현 계획을 설명합니다.

## 현재 단계: POC (Proof of Concept)

현재 뉴럴메모는 핵심 개념을 검증하기 위한 POC 단계에 있습니다. 이 단계에서는 다음 요소들에 집중합니다:

1. **웹 콘텐츠 공유 기능**: 모바일 브라우저나 앱에서 "공유" 기능을 통해 뉴럴메모로 콘텐츠를 전송
2. **핵심 개념 추출**: LLM API를 활용한 주요 키워드, 개념, 주장 추출
3. **기존 지식과 연결**: 벡터 임베딩과 코사인 유사도를 활용한 관계 매핑
4. **지식 그래프 탐색**: 수집된 지식들 간의 관계를 시각적 그래프로 탐색

## 개발 단계별 계획

### 1단계: 기초 기능 구현 (현재 ~ 2주차)

#### 백엔드
- [x] 프로젝트 기본 구조 설정
- [ ] 사용자 인증 시스템 구현
- [ ] 콘텐츠 캡처 API 개발
- [ ] 웹 콘텐츠 추출 엔진 통합 (Newspaper3k/Trafilatura)
- [ ] 기본 모델 정의 (Content, Concept, Connection)
- [ ] 개념 추출을 위한 OpenAI API 통합

#### 프론트엔드
- [ ] 모바일 앱 기본 UI 구현
- [ ] 사용자 인증 화면 구현
- [ ] 콘텐츠 캡처 및 보기 화면 구현

### 2단계: 핵심 기능 개선 (3~4주차)

#### 백엔드
- [ ] 개념 추출 알고리즘 개선
- [ ] 벡터 임베딩 생성 및 저장 기능 구현
- [ ] 코사인 유사도 기반 개념 연결 기능 구현
- [ ] 지식 그래프 API 개발

#### 프론트엔드
- [ ] 개념 탐색 화면 구현
- [ ] 지식 그래프 시각화 구현 (D3.js 또는 유사 라이브러리 활용)
- [ ] 개념 상세 보기 화면 구현

### 3단계: 확장 기능 구현 (5~8주차)

#### 백엔드
- [ ] 인사이트 생성 API 개발
- [ ] 학습 최적화 알고리즘 (망각 곡선 기반 복습) 구현
- [ ] 대화형 지식 탐색 API 개발
- [ ] 사용자 활동 분석 및 추천 시스템 구현

#### 프론트엔드
- [ ] 인사이트 화면 구현
- [ ] 복습 및 학습 화면 구현
- [ ] 대화형 탐색 인터페이스 구현
- [ ] 사용자 설정 및 기본 설정 화면 구현

### 4단계: 베타 출시 준비 (9~12주차)

#### 시스템 개선
- [ ] 성능 최적화 및 벤치마킹
- [ ] 데이터베이스 인덱싱 및 쿼리 최적화
- [ ] PostgreSQL로 데이터베이스 마이그레이션
- [ ] 캐싱 시스템 구현

#### 사용자 경험
- [ ] 사용자 피드백 수집 및 분석 시스템 구현
- [ ] 온보딩 프로세스 개선
- [ ] 도움말 및 문서 작성
- [ ] 버그 수정 및 안정화

## 향후 확장 계획

### 추가 데이터 소스 지원
- [ ] PDF 문서 분석
- [ ] 이미지 OCR 및 텍스트 추출
- [ ] 음성 메모 트랜스크립션
- [ ] 동영상 자막 분석

### 고급 AI 기능
- [ ] 개인화된 지식 추천 시스템
- [ ] 지식 간 새로운 연결 제안
- [ ] 다국어 지원 및 번역 통합
- [ ] 창작 지원 도구 (글쓰기, 아이디어 생성)

### 협업 기능
- [ ] 선택적 지식 공유
- [ ] 협업 지식 공간
- [ ] 공유 지식 그래프 시각화
- [ ] 지식 기여 및 검증 시스템

### 통합 기능
- [ ] 노션, 에버노트 등 지식 관리 도구와 통합
- [ ] 캘린더 앱과 연동한 학습 일정 관리
- [ ] API를 통한 서드파티 앱 연동
- [ ] 데스크톱 앱 개발

## 기술적 과제 및 연구 영역

### 확장성 문제
- 그래프 데이터베이스로의 마이그레이션 검토
- 사용자별 데이터 파티셔닝 전략
- 벡터 데이터베이스 성능 최적화

### 프라이버시 및 보안
- 종단간 암호화 구현
- 로컬 처리와 클라우드 처리의 최적 균형점 찾기
- 사용자 데이터 소유권 보장 방법

### 인공지능 개선
- 자체 호스팅 LLM 옵션 검토
- 개인화된 임베딩 모델 학습 방법 연구
- 설명 가능한 AI 접근 방식 통합

## 마일스톤 및 릴리스 계획

### 알파 릴리스 (12주차)
- 핵심 기능이 작동하는 내부 테스트 버전
- 제한된 사용자 그룹에게 배포
- 주요 버그 및 사용성 문제 식별

### 비공개 베타 (16주차)
- 초기 사용자 피드백을 반영한 개선 버전
- 초대 기반 사용자 확장
- 사용 패턴 모니터링 및 분석

### 공개 베타 (20주차)
- 안정성 및 성능이 향상된 버전
- 일반 사용자에게 개방
- 확장 기능 단계적 도입

### 정식 출시 (24주차)
- 완전한 기능을 갖춘 안정 버전
- 앱스토어 및 공식 채널을 통한 배포
- 마케팅 및 사용자 확보 활동

## 개발 우선순위 및 자원 할당

### 최우선 과제 (핵심 가치 구현에 필수적)
1. 웹 콘텐츠 캡처 및 처리 파이프라인
2. 개념 추출 및 벡터화 시스템
3. 지식 연결 및 그래프 탐색 기능

### 중요 과제 (사용자 경험 향상에 중요)
1. 직관적인 모바일 UI/UX
2. 성능 최적화 및 응답 시간 단축
3. 지식 그래프 시각화 개선

### 추가 과제 (차별화 요소)
1. 인사이트 생성 알고리즘
2. 학습 최적화 및 망각 방지 시스템
3. 다양한 데이터 소스 통합

## Django 구현 세부 계획

### 모델 설계 세부 사항

#### Content 모델 확장
```python
class Content(models.Model):
    # 기존 필드
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    body = models.TextField()
    source_url = models.URLField(blank=True, null=True)
    source_type = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # 추가 필드
    summary = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)  # 추출된 메타데이터 저장
    read_count = models.PositiveIntegerField(default=0)    # 읽은 횟수
    importance = models.FloatField(default=0.0)            # 중요도 점수
    tags = models.ManyToManyField('Tag', blank=True)
    
    # 매니저
    objects = models.Manager()
    
    # 메서드
    def extract_concepts(self):
        """내용에서 개념 추출 및 저장"""
        # LLM을 사용한 개념 추출 로직
        pass
    
    def update_importance(self):
        """중요도 점수 업데이트"""
        # 읽은 횟수, 개념 수, 생성 시간 등을 고려한 중요도 계산
        pass
    
    def get_related_contents(self, limit=5):
        """관련 콘텐츠 찾기"""
        # 개념을 통해 연결된 다른 콘텐츠 찾기
        pass
```

#### Concept 모델 확장
```python
class Concept(models.Model):
    # 기존 필드
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='concepts')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    confidence = models.FloatField(default=0.0)
    vector_embedding = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # 추가 필드
    category = models.CharField(max_length=50, blank=True)  # 개념 카테고리
    review_count = models.PositiveIntegerField(default=0)   # 복습 횟수
    last_reviewed = models.DateTimeField(null=True, blank=True)  # 마지막 복습 시간
    
    # 매니저
    objects = models.Manager()
    
    # 메서드
    def find_similar_concepts(self, threshold=0.8, limit=10):
        """유사한 개념 찾기"""
        # 벡터 임베딩 유사도 기반 검색
        pass
    
    def should_review(self):
        """복습이 필요한지 확인"""
        # 망각 곡선 기반 복습 시간 계산
        pass
    
    def generate_embedding(self):
        """개념에 대한 벡터 임베딩 생성"""
        # Sentence-BERT 등을 활용한 임베딩 생성
        pass
```

#### Connection 모델 확장
```python
class Connection(models.Model):
    # 기존 필드
    source = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name='outgoing_connections')
    target = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name='incoming_connections')
    similarity = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # 추가 필드
    relationship_type = models.CharField(max_length=50, blank=True)  # 관계 유형 (예: 'is-a', 'part-of')
    strength = models.FloatField(default=0.0)  # 연결 강도 (시간에 따라 변화)
    user_verified = models.BooleanField(default=False)  # 사용자가 확인한 연결인지
    
    # 매니저
    objects = models.Manager()
    
    # 메서드
    def update_strength(self, value=0.1):
        """연결 강도 업데이트"""
        # 사용자가 이 연결을 탐색할 때마다 강도 증가
        pass
```

### 새로운 모델 추가

#### Tag 모델
```python
class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
```

#### Insight 모델
```python
class Insight(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    concepts = models.ManyToManyField(Concept, related_name='insights')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
```

#### Review 모델
```python
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    concept = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name='reviews')
    reviewed_at = models.DateTimeField(auto_now_add=True)
    review_stage = models.PositiveSmallIntegerField(default=1)  # 복습 단계 (1-5)
    success = models.BooleanField(default=True)  # 성공적인 복습인지
    
    class Meta:
        ordering = ['-reviewed_at']
```

### 뷰 및 시리얼라이저 구현 계획

Django REST Framework를 활용하여 다음 패턴으로 API를 구현할 계획입니다:

1. 모델별 ViewSet 구현
2. 복잡한 비즈니스 로직은 시리얼라이저나 모델 메서드로 캡슐화
3. 필터링, 검색, 페이징 기능 통합

이 로드맵은 프로젝트의 진행 상황과 사용자 피드백에 따라 조정될 수 있습니다.