# 뉴럴메모 API 문서

이 문서는 뉴럴메모 시스템의 API 엔드포인트와 사용법을 설명합니다.

## 인증

모든 API 요청은 인증이 필요합니다. 인증은 JWT 토큰 기반으로 이루어집니다.

```
Authorization: Bearer <토큰>
```

### 로그인 (토큰 획득)

```
POST /api/auth/token/
Content-Type: application/json

{
  "username": "사용자이름",
  "password": "비밀번호"
}
```

**응답**:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 토큰 갱신

```
POST /api/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "갱신토큰"
}
```

**응답**:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## 콘텐츠 관리 API

### 콘텐츠 캡처

```
POST /api/content/capture/
Content-Type: application/json

{
  "url": "https://example.com/article",
  "source_type": "web"
}
```

또는 직접 콘텐츠 본문 제공:

```
POST /api/content/capture/
Content-Type: application/json

{
  "title": "콘텐츠 제목",
  "body": "콘텐츠 본문...",
  "source_type": "manual",
  "source_url": "https://example.com/source" (선택사항)
}
```

**응답**:
```json
{
  "id": 123,
  "title": "캡처된 콘텐츠 제목",
  "source_url": "https://example.com/article",
  "source_type": "web",
  "created_at": "2025-04-28T10:30:00Z",
  "processing_status": "pending"
}
```

### 콘텐츠 목록 조회

```
GET /api/content/
```

**쿼리 파라미터**:
- `page`: 페이지 번호 (기본값: 1)
- `page_size`: 페이지당 항목 수 (기본값: 10)
- `source_type`: 소스 타입으로 필터링
- `search`: 제목과 본문에서 검색
- `order_by`: 정렬 기준 (`created_at`, `-created_at` 등)

**응답**:
```json
{
  "count": 42,
  "next": "http://api.example.com/api/content/?page=2",
  "previous": null,
  "results": [
    {
      "id": 123,
      "title": "콘텐츠 제목",
      "source_url": "https://example.com/article",
      "source_type": "web",
      "created_at": "2025-04-28T10:30:00Z",
      "concepts_count": 5
    },
    // ... 추가 콘텐츠
  ]
}
```

### 콘텐츠 상세 조회

```
GET /api/content/{id}/
```

**응답**:
```json
{
  "id": 123,
  "title": "콘텐츠 제목",
  "body": "콘텐츠 본문...",
  "source_url": "https://example.com/article",
  "source_type": "web",
  "created_at": "2025-04-28T10:30:00Z",
  "concepts": [
    {
      "id": 456,
      "name": "알고리즘 편향성",
      "confidence": 0.92,
      "created_at": "2025-04-28T10:31:15Z"
    },
    // ... 추가 개념
  ]
}
```

### 콘텐츠 삭제

```
DELETE /api/content/{id}/
```

**응답**: 204 No Content

## 개념 관리 API

### 개념 목록 조회

```
GET /api/concepts/
```

**쿼리 파라미터**:
- `page`: 페이지 번호 (기본값: 1)
- `page_size`: 페이지당 항목 수 (기본값: 10)
- `search`: 개념 이름과 설명에서 검색
- `confidence`: 최소 신뢰도 값 (예: 0.8)
- `content_id`: 특정 콘텐츠에 연결된 개념만 필터링
- `order_by`: 정렬 기준 (`created_at`, `confidence` 등)

**응답**:
```json
{
  "count": 120,
  "next": "http://api.example.com/api/concepts/?page=2",
  "previous": null,
  "results": [
    {
      "id": 456,
      "name": "알고리즘 편향성",
      "confidence": 0.92,
      "created_at": "2025-04-28T10:31:15Z",
      "content": {
        "id": 123,
        "title": "콘텐츠 제목"
      },
      "connections_count": 8
    },
    // ... 추가 개념
  ]
}
```

### 개념 상세 조회

```
GET /api/concepts/{id}/
```

**응답**:
```json
{
  "id": 456,
  "name": "알고리즘 편향성",
  "description": "알고리즘 편향성에 대한 설명...",
  "confidence": 0.92,
  "created_at": "2025-04-28T10:31:15Z",
  "content": {
    "id": 123,
    "title": "콘텐츠 제목",
    "source_url": "https://example.com/article"
  },
  "connections": [
    {
      "id": 789,
      "target": {
        "id": 457,
        "name": "데이터 편향"
      },
      "similarity": 0.85
    },
    // ... 추가 연결
  ]
}
```

### 개념 업데이트

```
PATCH /api/concepts/{id}/
Content-Type: application/json

{
  "name": "업데이트된 개념 이름",
  "description": "업데이트된 설명..."
}
```

**응답**:
```json
{
  "id": 456,
  "name": "업데이트된 개념 이름",
  "description": "업데이트된 설명...",
  "confidence": 0.92,
  "created_at": "2025-04-28T10:31:15Z"
}
```

### 개념 삭제

```
DELETE /api/concepts/{id}/
```

**응답**: 204 No Content

## 연결 관리 API

### 연결 생성

```
POST /api/connections/
Content-Type: application/json

{
  "source_id": 456,
  "target_id": 457,
  "similarity": 0.85
}
```

**응답**:
```json
{
  "id": 789,
  "source": {
    "id": 456,
    "name": "알고리즘 편향성"
  },
  "target": {
    "id": 457,
    "name": "데이터 편향"
  },
  "similarity": 0.85,
  "created_at": "2025-04-28T11:15:00Z"
}
```

### 연결 목록 조회

```
GET /api/connections/
```

**쿼리 파라미터**:
- `page`: 페이지 번호 (기본값: 1)
- `page_size`: 페이지당 항목 수 (기본값: 10)
- `source_id`: 특정 소스 개념의 연결만 필터링
- `target_id`: 특정 대상 개념의 연결만 필터링
- `min_similarity`: 최소 유사도 값 (예: 0.7)

**응답**:
```json
{
  "count": 350,
  "next": "http://api.example.com/api/connections/?page=2",
  "previous": null,
  "results": [
    {
      "id": 789,
      "source": {
        "id": 456,
        "name": "알고리즘 편향성"
      },
      "target": {
        "id": 457,
        "name": "데이터 편향"
      },
      "similarity": 0.85,
      "created_at": "2025-04-28T11:15:00Z"
    },
    // ... 추가 연결
  ]
}
```

### 연결 삭제

```
DELETE /api/connections/{id}/
```

**응답**: 204 No Content

## 지식 그래프 API

### 지식 그래프 조회

```
GET /api/knowledge-graph/
```

**쿼리 파라미터**:
- `central_concept_id`: 중심 개념 ID (지정하지 않으면 전체 그래프)
- `depth`: 탐색 깊이 (기본값: 1)
- `min_similarity`: 최소 유사도 값 (기본값: 0.7)
- `limit`: 반환할 최대 노드 수 (기본값: 100)

**응답**:
```json
{
  "nodes": [
    {
      "id": 456,
      "name": "알고리즘 편향성",
      "confidence": 0.92,
      "group": 1
    },
    {
      "id": 457,
      "name": "데이터 편향",
      "confidence": 0.88,
      "group": 1
    },
    // ... 추가 노드
  ],
  "links": [
    {
      "source": 456,
      "target": 457,
      "value": 0.85
    },
    // ... 추가 링크
  ]
}
```

### 인사이트 생성

```
POST /api/insights/generate/
Content-Type: application/json

{
  "concept_ids": [456, 457, 458],
  "save_insight": true
}
```

**응답**:
```json
{
  "summary": "알고리즘 편향성, 데이터 편향, AI 윤리 개념들은 모두 인공지능 시스템의 공정성과 책임성을 다루고 있습니다...",
  "patterns": [
    "이 세 개념은 모두 기술의 사회적 영향에 초점을 맞추고 있습니다.",
    "데이터 품질과 알고리즘 설계가 윤리적 결과에 직접적인 영향을 미칩니다.",
    "모든 개념이 다학제적 접근 방식의 중요성을 강조합니다."
  ],
  "questions": [
    "AI 시스템에서 편향성을 발견했을 때 어떤 실용적인 완화 전략을 적용할 수 있을까요?",
    "알고리즘 투명성과 상업적 이익 사이의 균형을 어떻게 맞출 수 있을까요?"
  ],
  "related_topics": [
    "AI 거버넌스",
    "알고리즘 감사",
    "공정성 지표"
  ]
}
```

## 오류 응답

모든 API는 다음과 같은 형식으로 오류를 반환합니다:

```json
{
  "detail": "오류 메시지"
}
```

또는 필드별 오류:

```json
{
  "field_name": [
    "이 필드에 대한 오류 메시지"
  ]
}
```

## 상태 코드

- `200 OK`: 요청 성공 (GET)
- `201 Created`: 리소스 생성 성공 (POST)
- `204 No Content`: 리소스 삭제 성공 (DELETE)
- `400 Bad Request`: 잘못된 요청
- `401 Unauthorized`: 인증 실패
- `403 Forbidden`: 권한 없음
- `404 Not Found`: 리소스 없음
- `500 Internal Server Error`: 서버 오류