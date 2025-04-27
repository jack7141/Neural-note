import openai
from openai import OpenAI
from rest_framework import viewsets
from rest_framework.serializers import Serializer
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED
from newspaper import Article

import json

from api.versioned.v1.capture.serializers import CaptureSerializer
import requests
from bs4 import BeautifulSoup

from concept.models import ConceptDomain


OPENAI_API_KEY = ""

def process_core_themes(analysis_result):
    """
    Core themes의 상위 도메인을 LLM을 통해 결정
    """
    categories = analysis_result.get('category', [])
    core_themes = analysis_result.get('core_themes', [])

    # 상위 도메인 결정을 위한 추가 프롬프트
    domain_prompt = f"""
    다음 core themes와 기존 카테고리들을 고려하여 가장 적절한 상위 도메인을 선택하세요:

    Core Themes: {core_themes}
    기존 카테고리들: {categories}

    Core Themes의 상위 카테고리를 {categories}에서 선택하고, 그 이유를 간단히 설명하세요. 
    출력 형식:
    {{
        "parent_domain": "", // 선택된 상위 도메인
        "reasoning": ""       // 선택 이유
    }}
    
    출력은 추가 설명 없이 JSON 객체로 엄격하게 반환하세요.
    """

    try:
        # OpenAI API 호출
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        domain_completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "도메인 분류 도우미입니다."},
                {"role": "user", "content": domain_prompt}
            ],
            response_format={"type": "json_object"}
        )

        # 응답 처리
        domain_response = json.loads(domain_completion.choices[0].message.content)
        parent_domain_name = domain_response.get('parent_domain')

        # 부모 도메인 찾기 또는 생성
        parent_domain = ConceptDomain.objects.filter(name=parent_domain_name).first()
        if not parent_domain:
            parent_domain = ConceptDomain.objects.create(
                code=parent_domain_name.replace(' ', '_').lower(),
                name=parent_domain_name,
                description=f"{parent_domain_name} 관련 주제"
            )

    except Exception as e:
        # 예외 발생 시 기본값 사용
        print(f"도메인 결정 중 오류: {e}")
        parent_domain = ConceptDomain.objects.filter(name=categories[0]).first()

    # Core themes 처리
    processed_themes = []
    for theme in core_themes:
        # 이미 존재하는 도메인인지 확인
        existing_domain = ConceptDomain.objects.filter(name=theme).first()

        if not existing_domain:
            # 새로운 leaf 도메인 생성
            new_domain = ConceptDomain.objects.create(
                code=theme.replace(' ', '_').lower(),
                name=theme,
                parent=parent_domain,  # 결정된 상위 도메인과 연결
                description=f"{theme} 관련 세부 주제"
            )
            processed_themes.append(theme)
        else:
            processed_themes.append(existing_domain.name)

    return processed_themes


class StatusViewSet(viewsets.ReadOnlyModelViewSet):
    """
    status: 상태 체크

    Kibana Heartbeat 상태 체크용 API 입니다.
    """
    permission_classes = [AllowAny, ]
    serializer_class = CaptureSerializer

    """
    개념이 속한 가장 적절한 도메인 또는 주제 분야를 판단하고, 그에 맞는 벡터 표현을 생성하세요. -> 먼저 도메인 관련 DB를 만들고 아무것도 포함되지 않으면 생성하는 로직이 있어야할듯
    가능한 도메인:
    1. 통신/네트워크 기술
    2. 사이버 보안
    3. 환경/재활용
    4. IT 기기/가전
    5. 에너지 기술
    6. 재난 대응/구호
    7. 정책/규제
    8. 연구개발/혁신
    """

    def post(self, request, *args, **kwargs):
        url = "https://n.news.naver.com/mnews/article/032/0003365907"
        serializer = self.get_serializer(*args, **kwargs).data
        # article = Article(url, language='ko')  # 한국어 지정
        # article.download()
        # article.parse()
        # content = article.text
        # title = article.title
        # print(f"Title: {title}")
        # print(f"Content length: {len(content)}")
        # print(f"Content preview: {content[:200]}")  # 앞부분 200자만 출력
        # requests로 페이지 다운로드
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers)

        # BeautifulSoup으로 파싱
        soup = BeautifulSoup(response.text, "html.parser")

        # 제목 추출
        title_tag = soup.find('title')
        title = title_tag.get_text(strip=True) if title_tag else 'No title found'

        # 본문 추출
        content_tag = soup.find('div', id='dic_area') or soup.find('div', id='contents')
        content = content_tag.get_text(separator="\n", strip=True) if content_tag else ''

        # 결과 출력
        print(f"Title: {title}")
        print(f"Content length: {len(content)}")
        print(f"Content preview: {content[:200]}")  # 앞부분 200자만 출력
        if not content:
            return Response({"error": "분석할 콘텐츠가 필요합니다."}, status=400)
        # GPT 프롬프트 구성
        # GPT 프롬프트 구성
        leaf_domains = list(ConceptDomain.objects.filter(children__isnull=True).values_list('name', flat=True))
        prompt = f"""
        다음 텍스트를 한국어로 분석하고 다음 정보를 무조건 한국어로 추출하세요:

        1. 텍스트를 분석하고 다음 정보를 추출하세요.
        2. 모든 응답은 **리스트 형식**으로 제공해야 합니다 (단 하나의 항목이라도 리스트로 반환).
        3. 다음 영어 키를 정확히 사용하여 응답하세요:
        4. 다음 기존 카테고리와 비교하여 가장 적합한 카테고리를 선택하세요(단 어디에도 포함되지 않다면 새로운 개념을 제안하세요).:
        {list(ConceptDomain.objects.all().values_list('name', flat=True))}
        5. 다음 기존 leaf 개념들 중에서 주요 개념을 선택하세요(단 어디에도 포함되지 않다면 새로운 개념을 제안하세요). :
        {leaf_domains}
        {{
            "category": [],         // 콘텐츠 카테고리 (예: 기술, 과학, 경제, 교육 등)
            "core_themes": [],      // 서브 카테고리 주제/토픽 -> tag 개념으로 수정해서 tag 별로 개념들을 엮는게 나으려나?
            "main_concepts": [      // 주요 개념 (형식: {{ "name": "개념 이름", "confidence": 95 }})
            ],
            "emotional_tone": [],   // 감정 톤 (예: 객관적, 주관적, 비판적, 중립적, 긍정적 등)
            "mention_point_of_view": [] // 언급된 관점 (예: 기업 관점, 소비자 관점)
        }}

        출력은 추가 설명 없이 JSON 객체로 엄격하게 반환하세요.

        텍스트:
        {content}
        """

        try:
            # OpenAI API 호출 설정
            client = openai.OpenAI(api_key=OPENAI_API_KEY)

            # GPT API 호출
            completion = client.chat.completions.create(
                model="gpt-4o",  # 또는 사용 가능한 모델
                messages=[
                    {"role": "system", "content": "주어진 텍스트를 분석하여 구조화된 JSON으로 응답하는 도우미입니다."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )

            # 응답 추출 및 JSON 파싱
            gpt_response = completion.choices[0].message.content
            analysis_result = json.loads(gpt_response)
            refined_core_themes = process_core_themes(analysis_result)
            # 9. 응답 반환
            return Response({
                "id": content.id,
                "title": content.title,
                "message": "콘텐츠 분석 및 저장이 완료되었습니다."
            }, status=HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": f"저장 중 오류가 발생했습니다: {str(e)}"}, status=500)

        return Response(status=HTTP_200_OK)

