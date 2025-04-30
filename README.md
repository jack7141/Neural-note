# 🧠 NeuralMemo: AI 증강 지식 관리 시스템

## 프로젝트 소개

NeuralMemo는 인간의 두뇌를 디지털로 확장하는 혁신적인 지식 관리 플랫폼입니다. 정보 과잉의 시대에 단순히 정보를 저장하는 것이 아니라, 정보 간의 맥락과 연결성을 파악하여 더 깊은 통찰력을 제공합니다.

### 🚀 핵심 가치

- **무노력 지식 획득**: 읽기만 해도 자동으로 핵심 개념 추출
- **연결 지향적 사고**: 분절된 정보가 아닌 연결된 지식 네트워크 구축
- **개인화된 인사이트**: 개인의 학습 패턴과 관심사에 맞춘 지식 연결
- **프라이버시 우선**: 민감한 개인 지식 데이터의 철저한 보호

## 🛠 기술 스택

### 백엔드
- Django
- Django REST Framework
- PostgreSQL
- Celery
- Redis

### 프론트엔드
- React Native
- React
- TailwindCSS

### AI/ML
- Hugging Face Transformers
- OpenAI GPT API
- Sentence-BERT
- spaCy

## 🔧 설치 및 설정

### 사전 요구사항

- Python 3.9+
- Node.js 16+
- PostgreSQL
- Redis

### 백엔드 설치

1. 가상 환경 생성
```bash
python3 -m venv venv
source venv/bin/activate
```

2. 의존성 설치
```bash
pip install -r requirements.txt
```

3. 데이터베이스 마이그레이션
```bash
python manage.py migrate
```

4. 개발 서버 실행
```bash
python manage.py runserver
```

### 프론트엔드 설치

1. 의존성 설치
```bash
cd frontend
npm install
```

2. 개발 서버 실행
```bash
npm start
```

## 🚀 주요 기능

- 웹, PDF, 문서에서 지식 자동 캡처
- AI 기반 핵심 개념 추출
- 지식 그래프 시각화
- 개인화된 학습 인사이트 제공
- 망각 곡선 기반 복습 시스템

## 🗺 로드맵

현재 개발 단계는 POC(Proof of Concept)입니다. 주요 마일스톤:

- [x] 기본 프로젝트 구조 설정
- [ ] 사용자 인증 시스템
- [ ] 콘텐츠 캡처 API
- [ ] 개념 추출 엔진
- [ ] 지식 그래프 시각화

## 🤝 기여하기

1. 저장소 포크
2. 기능 브랜치 생성 (`git checkout -b feature/amazing-feature`)
3. 변경사항 커밋 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치에 푸시 (`git push origin feature/amazing-feature`)
5. 풀 리퀘스트 열기

## 📄 라이선스

MIT 라이선스에 따라 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 문의

프로젝트 링크: [GitHub 저장소 링크]
문의 이메일: [연락처 이메일]

---

🌟 **지식은 연결될 때 진정한 힘을 발휘합니다** 🌟
