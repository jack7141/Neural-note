import openai
from openai import OpenAI
from rest_framework import viewsets
from rest_framework.serializers import Serializer
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED
from newspaper import Article

import json

from knowledgesnode.models import ContentAnalysis, CoreTheme, RelatedDomain, KeyTerm, KeyClaim, Concept
import requests
from bs4 import BeautifulSoup

class StatusViewSet(viewsets.ReadOnlyModelViewSet):
    """
    status: 상태 체크

    Kibana Heartbeat 상태 체크용 API 입니다.
    """
    permission_classes = [AllowAny, ]
    serializer_class = Serializer

    def status(self, request, *args, **kwargs):
        url = "https://n.news.naver.com/mnews/hotissue/article/029/0002944474?type=series&cid=2002644"
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
        다음 텍스트를 분석하여 한국말로 아래 항목들을 추출해주세요:

        1. 텍스트를 분석하여 다음 정보를 추출하세요.
        2. 모든 응답은 리스트 형식으로 제공해야 합니다(단일 값도 리스트에 담아 반환).
        3. 값을 추출할 수 없더라도 카테고리는 반드시 지정해야 합니다(적합한 카테고리가 없으면 '기타'로 분류).
        4. 신뢰도 점수는 숫자만 포함하세요(% 기호 없이).

        다음 JSON 형식으로 응답하되, 영어 키 값을 사용하세요:
        {{
          "category": [], // 콘텐츠 카테고리 (예: 기술, 과학, 경제, 교육 등)
          "core_themes": [], // 핵심 주제 (텍스트의 가장 중심이 되는 주제들)
          "main_concepts": [], // 주요 개념 (각 항목은 {{name: "개념명", confidence: 95}} 형식)
          "key_claims": [], // 핵심 주장/관점 
          "related_domains": [], // 관련 도메인 (해당 내용이 연관될 수 있는 다른 지식 분야)
          "emotional_tone": [], // 감정 톤 (객관적, 주관적, 비판적, 중립적, 긍정적 등)
          "key_terms": [], // 중요 용어나 전문 용어
          "temporal_context": [] // 시간적 맥락 (과거, 현재, 미래 중심 또는 특정 시점 언급)
        }}

        텍스트: {content.content}
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

