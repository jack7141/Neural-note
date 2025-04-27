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
from knowledgesnode.models import ContentAnalysis, CoreTheme, RelatedDomain, KeyTerm, KeyClaim, Concept
import requests
from bs4 import BeautifulSoup

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
        url = "https://n.news.naver.com/mnews/article/014/0005341698"
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
        from knowledgesnode.models import Content
        content = Content.objects.create(title=title, content=content, source_url=url)
        # GPT 프롬프트 구성
        prompt = f"""
        The following text should be analyzed in Korean and the following information should be extracted:

        1. Analyze the text and extract the following information.
        2. All responses must be provided in a **list format** (even if there is only one item, return it as a list).
        3. Use **English keys** exactly as specified below:
        {{
            "category": [],         // Content categories (e.g., technology, science, economy, education, etc.)
            "core_themes": [],       // Core themes/topics
            "main_concepts": [       // Main concepts (each item must be in the format {{ "name": "concept name", "confidence": 95 }})
            ],
            "emotional_tone": [],    // Emotional tone (e.g., objective, subjective, critical, neutral, positive, etc.)
            "mention_point_of_view": [] // Perspective mentioned (e.g., corporate perspective, consumer perspective)
        }}

        Return the entire output strictly as a JSON object without any additional explanation or text.

        Text:
        {Content.content}
        """

        try:
            # OpenAI API 호출 설정
            OPENAI_API_KEY = "SECRET"
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
            content_analysis = ContentAnalysis.objects.create(
                content=content,
                category=analysis_result.get('category')[0],  # 첫 번째 카테고리 저장
                emotional_tone=analysis_result.get('emotional_tone')[0],  # 첫 번째 감정톤 저장
                temporal_context=analysis_result.get('temporal_context')[0],  # 첫 번째 시간적 맥락 저장
                raw_analysis=analysis_result  # 원본 JSON 저장 (옵션)
            )

            # 4. 핵심 주제 저장
            for theme in analysis_result.get('core_themes', []):
                CoreTheme.objects.create(
                    content_analysis=content_analysis,
                    theme=theme
                )

            # 5. 개념 객체 생성 및 저장
            concepts = []
            for concept_data in analysis_result.get('main_concepts', []):
                # 개선된 형식으로 이미 confidence는 숫자로 제공됨
                concept = Concept.objects.create(
                    content_analysis=content_analysis,
                    name=concept_data["name"],
                    confidence=concept_data["confidence"] / 100.0,  # 0-1 범위로 변환
                    category=analysis_result.get('category')[0]  # 첫 번째 카테고리 사용
                )
                concepts.append(concept)

            # 6. 핵심 주장 저장
            for claim in analysis_result.get('key_claims', []):
                KeyClaim.objects.create(
                    content_analysis=content_analysis,
                    claim=claim
                )

            # 7. 관련 도메인 저장
            for domain in analysis_result.get('related_domains', []):
                RelatedDomain.objects.create(
                    content_analysis=content_analysis,
                    domain=domain
                )

            # 8. 중요 용어 저장
            for term in analysis_result.get('key_terms', []):
                KeyTerm.objects.create(
                    content_analysis=content_analysis,
                    term=term
                )

            # 9. 응답 반환
            return Response({
                "id": content.id,
                "title": content.title,
                "analysis_id": content_analysis.id,
                "concepts": [{"id": c.id, "name": c.name, "confidence": c.confidence} for c in concepts],
                "message": "콘텐츠 분석 및 저장이 완료되었습니다."
            }, status=HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": f"저장 중 오류가 발생했습니다: {str(e)}"}, status=500)

        return Response(status=HTTP_200_OK)

