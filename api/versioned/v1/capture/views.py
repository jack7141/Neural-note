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
        {content}
        """

        try:
            # OpenAI API 호출 설정
            OPENAI_API_KEY = ""
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

            # 9. 응답 반환
            return Response({
                "id": content.id,
                "title": content.title,
                "message": "콘텐츠 분석 및 저장이 완료되었습니다."
            }, status=HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": f"저장 중 오류가 발생했습니다: {str(e)}"}, status=500)

        return Response(status=HTTP_200_OK)

