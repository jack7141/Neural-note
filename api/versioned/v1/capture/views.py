import json
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST

import openai
from openai import OpenAI

from api.versioned.v1.capture.serializers import CaptureSerializer
from api.versioned.v1.utils.neo4j_client import Neo4jClient

from article.models import Article, ArticleConcept, ArticleEntity, ArticleEvent, ArticleRelationship
from concept.models import ConceptDomain, Concept, ConceptRelationship
from event.models import Event
from entity.models import Entity

logger = logging.getLogger(__name__)
OPENAI_API_KEY = settings.OPENAI_API_KEY

class CaptureViewSet(viewsets.ModelViewSet):
    """
    기사 캡처 및 분석 API
    
    웹 페이지에서 기사를 캡처하고 분석하는 API입니다.
    """
    permission_classes = [IsAuthenticated, ]
    serializer_class = CaptureSerializer
    queryset = Article.objects.all()
    
    def get_queryset(self):
        """현재 사용자의 기사만 반환"""
        return Article.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """기사 캡처 및 분석"""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
        url = serializer.validated_data.get('url')
        
        # 웹 페이지 내용 가져오기
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # 제목 추출
            title_tag = soup.find('title') or soup.find('h1')
            title = title_tag.get_text(strip=True) if title_tag else 'No title found'

            # 본문 추출 (뉴스 사이트마다 다를 수 있음)
            content_tag = soup.find('div', id='dic_area') or soup.find('div', id='contents') or soup.find('article')
            content = content_tag.get_text(separator="\n", strip=True) if content_tag else ''

            # 언론사 추출 시도
            source = None
            meta_publisher = soup.find('meta', property='og:site_name')
            if meta_publisher:
                source = meta_publisher.get('content')
            
            # 발행일 추출 시도
            published_date = None
            meta_date = soup.find('meta', property='article:published_time')
            if meta_date:
                date_str = meta_date.get('content')
                try:
                    published_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except:
                    pass

            # 콘텐츠가 없으면 에러 반환
            if not content:
                return Response({"error": "분석할 콘텐츠가 필요합니다."}, status=HTTP_400_BAD_REQUEST)
            
            # 기사 객체 생성

            article = Article.objects.create(
                user=request.user,
                title=title,
                url=url,
                content=content,
                source=source or '',
                published_date=published_date,
                processing_status='processing'
            )
            
            # 비동기로 처리하는 것이 좋지만, 예제에서는 동기적으로 처리
            self.analyze_and_process_article(article)
            
            return Response({
                "id": article.id,
                "title": article.title,
                "message": "콘텐츠 분석 및 저장이 완료되었습니다."
            }, status=HTTP_201_CREATED)
            
        except requests.RequestException as e:
            return Response({"error": f"웹 페이지를 가져오는데 실패했습니다: {str(e)}"}, status=HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"기사 처리 중 오류 발생: {str(e)}")
            return Response({"error": f"처리 중 오류가 발생했습니다: {str(e)}"}, status=HTTP_400_BAD_REQUEST)
    
    def analyze_and_process_article(self, article):
        """기사 분석 및 처리"""
        try:
            # GPT 프롬프트 구성
            leaf_domains = list(ConceptDomain.objects.filter(children__isnull=True).values_list('name', flat=True))
            existing_events = list(Event.objects.all().values_list('name', flat=True)[:10])
            
            prompt = f"""
            다음 텍스트를 한국어로 분석하고 다음 정보를 무조건 한국어로 추출하세요:

            1. 모든 응답은 JSON 형식으로 제공해야 합니다.
            2. 다음 영어 키를 정확히 사용하여 응답하세요:
            {{
                "category": [],           // 콘텐츠 카테고리 (예: 기술, 과학, 경제, 교육 등)
                "core_themes": [],        // 주요 주제/토픽 (2-5개)
                "main_concepts": [        // 주요 개념 (형식: {{ "name": "개념 이름", "description": "간략한 설명", "confidence": 95 }})
                ],
                "entities": [             // 기사에 등장하는 주요 엔티티 (형식: {{ "name": "엔티티 이름", "entity_type": "조직/인물/제품/기술", "mention_count": 3 }})
                ],
                "event_info": {{          // 기사가 다루는 이벤트 정보
                    "event_name": "",     // 이벤트 이름 (예: "SKT 유심 해킹 사건")
                    "event_date": "",     // 이벤트 발생 날짜 (정확한 YYYY-MM-DD 형식만 입력, 없으면 빈 문자열)
                    "event_type": "",     // 이벤트 유형 (예: "사이버 보안 사고")
                    "description": ""     // 이벤트 간략 설명
                }},
                "related_concepts": [     // 기사에 직접 언급되지 않았지만 관련된 개념들 (형식: {{ "name": "개념 이름", "confidence": 80 }})
                ],
                "concept_relationships": [ // 개념 간 관계 (형식: {{ "source": "개념1", "target": "개념2", "relationship_type": "RELATED_TO/IS_A/PART_OF", "weight": 0.9 }})
                ],
                "summary": "",            // 기사 요약 (3-5문장)
                "related_to_existing_events": [] // 이 기사가 관련된 기존 이벤트 목록 (아래 목록에서 선택)
            }}

            이 기사가 다음 기존 이벤트와 관련이 있는지 평가하세요:
            {existing_events}

            적절한 도메인 분류:
            {list(ConceptDomain.objects.all().values_list('name', flat=True))}

            기존에 추출된 주요 개념(비슷한 개념이 있다면 재사용하는 것이 좋습니다):
            {list(Concept.objects.all().values_list('name', flat=True)[:20])}

            리프 도메인 목록(가장 구체적인 도메인):
            {leaf_domains}

            텍스트:
            {article.content}
            """

            # OpenAI API 호출
            client = OpenAI(api_key=OPENAI_API_KEY)
            
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
            
            # 분석 결과를 DB에 저장
            with transaction.atomic():
                # 요약문 저장
                article.summary = analysis_result.get('summary', '')
                
                # 카테고리 저장
                for category_name in analysis_result.get('category', []):
                    domain, created = ConceptDomain.objects.get_or_create(name=category_name)
                    article.domains.add(domain)
                
                # 주요 개념 저장
                for concept_data in analysis_result.get('main_concepts', []):
                    concept, created = Concept.objects.get_or_create(
                        name=concept_data['name'],
                        defaults={
                            'description': concept_data.get('description', ''),
                            'confidence': concept_data.get('confidence', 0.0)
                        }
                    )
                    
                    # 개념과 기사 연결
                    ArticleConcept.objects.create(
                        article=article,
                        concept=concept,
                        confidence=concept_data.get('confidence', 0.0),
                        is_key_concept=True
                    )
                
                # 엔티티 저장
                for entity_data in analysis_result.get('entities', []):
                    entity, created = Entity.objects.get_or_create(
                        name=entity_data['name'],
                        entity_type=entity_data.get('entity_type', '기타'),
                        defaults={
                            'description': entity_data.get('description', '')
                        }
                    )
                    
                    # 엔티티와 기사 연결
                    ArticleEntity.objects.create(
                        article=article,
                        entity=entity,
                        confidence=1.0,
                        mention_count=entity_data.get('mention_count', 1)
                    )
                
                # 이벤트 저장
                event_info = analysis_result.get('event_info', {})
                if event_info and event_info.get('event_name'):
                    # 날짜 값 처리 - 텍스트가 아닌 유효한 날짜 형식만 받음
                    event_date = None
                    if event_info.get('event_date'):
                        try:
                            # YYYY-MM-DD 형식 검증
                            date_str = event_info.get('event_date')
                            if date_str and isinstance(date_str, str) and len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
                                event_date = date_str
                        except:
                            pass
                            
                    event, created = Event.objects.get_or_create(
                        name=event_info['event_name'],
                        defaults={
                            'description': event_info.get('description', ''),
                            'event_date': event_date,
                            'event_type': event_info.get('event_type', '')
                        }
                    )
                    
                    # 이벤트와 기사 연결
                    ArticleEvent.objects.create(
                        article=article,
                        event=event,
                        relationship_type='PART_OF',
                        confidence=1.0
                    )
                    
                    # 이벤트에 도메인 연결
                    if article.domains.exists():
                        event.domain = article.domains.first()
                        event.save()
                
                # 관련된 기존 이벤트 연결
                for event_name in analysis_result.get('related_to_existing_events', []):
                    try:
                        event = Event.objects.get(name=event_name)
                        ArticleEvent.objects.create(
                            article=article,
                            event=event,
                            relationship_type='RELATED_TO',
                            confidence=0.8
                        )
                    except Event.DoesNotExist:
                        continue
                
                # 개념 간 관계 저장
                for rel_data in analysis_result.get('concept_relationships', []):
                    try:
                        source_concept, _ = Concept.objects.get_or_create(name=rel_data['source'])
                        target_concept, _ = Concept.objects.get_or_create(name=rel_data['target'])
                        
                        ConceptRelationship.objects.create(
                            source_concept=source_concept,
                            target_concept=target_concept,
                            relationship_type=rel_data.get('relationship_type', 'RELATED_TO'),
                            weight=rel_data.get('weight', 0.5)
                        )
                    except Exception as e:
                        logger.warning(f"개념 관계 저장 중 오류: {str(e)}")
                
                # 관련 기사 찾기 및 관계 설정
                self.find_and_link_related_articles(article)
                
                # Neo4j에 데이터 저장
                self.save_to_neo4j(article)
                
                # 처리 완료로 상태 변경
                article.processing_status = 'completed'
                article.save()
                
            return True
            
        except Exception as e:
            logger.error(f"기사 분석 중 오류 발생: {str(e)}")
            article.processing_status = 'failed'
            article.error_message = str(e)
            article.save()
            return False
    
    def find_and_link_related_articles(self, article):
        """관련 기사 찾기 및 연결"""
        try:
            # 같은 이벤트를 다루는 기사 찾기
            related_by_event = Article.objects.filter(
                events__in=article.events.all()
            ).exclude(id=article.id).distinct()
            
            # 관련 기사와의 관계 설정
            for related_article in related_by_event:
                ArticleRelationship.objects.create(
                    source_article=article,
                    target_article=related_article,
                    relationship_type='RELATED_TO',
                    similarity_score=0.8
                )
            
            # 유사한 개념을 다루는 기사 찾기
            article_concepts = article.concepts.all()
            if article_concepts:
                related_by_concept = Article.objects.filter(
                    concepts__in=article_concepts
                ).exclude(id=article.id).distinct()
                
                for related_article in related_by_concept:
                    # 중복 방지
                    if not ArticleRelationship.objects.filter(
                        source_article=article,
                        target_article=related_article
                    ).exists():
                        common_concepts = article.concepts.filter(
                            id__in=related_article.concepts.values_list('id', flat=True)
                        ).count()
                        
                        # 공통 개념이 많을수록 유사도 높음
                        similarity = min(0.9, 0.5 + (common_concepts / 10))
                        
                        ArticleRelationship.objects.create(
                            source_article=article,
                            target_article=related_article,
                            relationship_type='RELATED_BY_CONCEPT',
                            similarity_score=similarity
                        )
            
            return True
            
        except Exception as e:
            logger.error(f"관련 기사 연결 중 오류 발생: {str(e)}")
            return False
    
    def save_to_neo4j(self, article):
        """Neo4j에 데이터 저장"""
        try:
            neo4j_client = Neo4jClient()
            
            # Neo4j 연결이 없을 경우 작업 스킵
            if not neo4j_client.graph:
                logger.warning("Neo4j 연결이 없어 그래프 저장을 건너뜁니다.")
                return False
            
            # 기사 노드 생성
            neo4j_client.create_article_node(article)
            
            # 개념 노드 생성 및 연결
            for article_concept in ArticleConcept.objects.filter(article=article):
                neo4j_client.create_concept_node(article_concept.concept)
                neo4j_client.create_article_concept_relationship(article_concept)
            
            # 엔티티 노드 생성 및 연결
            for article_entity in ArticleEntity.objects.filter(article=article):
                neo4j_client.create_entity_node(article_entity.entity)
                neo4j_client.create_article_entity_relationship(article_entity)
            
            # 이벤트 노드 생성 및 연결
            for article_event in ArticleEvent.objects.filter(article=article):
                neo4j_client.create_event_node(article_event.event)
                neo4j_client.create_article_event_relationship(article_event)
            
            # 기사 간 관계 저장
            for article_relationship in ArticleRelationship.objects.filter(source_article=article):
                neo4j_client.create_article_relationship(article_relationship)
            
            # 개념 간 관계 저장
            concept_ids = ArticleConcept.objects.filter(article=article).values_list('concept_id', flat=True)
            concept_relationships = ConceptRelationship.objects.filter(
                source_concept_id__in=concept_ids,
                target_concept_id__in=concept_ids
            )
            
            for concept_relationship in concept_relationships:
                neo4j_client.create_concept_relationship(concept_relationship)
            
            return True
            
        except Exception as e:
            logger.error(f"Neo4j 저장 중 오류 발생: {str(e)}")
            # Neo4j 저장은 실패해도 전체 처리는 성공으로 간주
            return True
    
    @action(detail=True, methods=['get'])
    def related_articles(self, request, pk=None):
        """관련 기사 조회"""
        try:
            article = self.get_object()
            
            # 관련 기사 조회 (Django ORM)
            related = ArticleRelationship.objects.filter(source_article=article)
            
            result = []
            for rel in related:
                result.append({
                    'id': rel.target_article.id,
                    'title': rel.target_article.title,
                    'relationship_type': rel.relationship_type,
                    'similarity_score': rel.similarity_score,
                    'url': rel.target_article.url
                })
            
            # Neo4j에서 추가 관련 기사 조회
            neo4j_client = Neo4jClient()
            neo4j_related = neo4j_client.find_similar_articles(article.id)
            
            # 중복 제거하면서 Neo4j 결과 추가
            existing_ids = [item['id'] for item in result]
            for item in neo4j_related:
                if item['article_id'] not in existing_ids:
                    try:
                        related_article = Article.objects.get(id=item['article_id'])
                        result.append({
                            'id': related_article.id,
                            'title': related_article.title,
                            'relationship_type': 'RELATED_TO',
                            'similarity_score': item.get('common_events', 0) / 10,
                            'url': related_article.url
                        })
                    except Article.DoesNotExist:
                        continue
            
            return Response(result, status=HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def knowledge_graph(self, request, pk=None):
        """기사의 지식 그래프 조회"""
        try:
            article = self.get_object()
            
            # Neo4j에서 지식 그래프 조회
            neo4j_client = Neo4jClient()
            graph_data = neo4j_client.get_article_knowledge_graph(article.id)
            
            if not graph_data:
                # Fallback: Django ORM으로 간단한 그래프 생성
                nodes = []
                edges = []
                
                # 기사 노드
                article_node = {
                    'id': f"a_{article.id}",
                    'label': 'Article',
                    'title': article.title,
                    'url': article.url
                }
                nodes.append(article_node)
                
                # 개념 노드 및 엣지
                for ac in ArticleConcept.objects.filter(article=article):
                    concept_node = {
                        'id': f"c_{ac.concept.id}",
                        'label': 'Concept',
                        'name': ac.concept.name,
                        'description': ac.concept.description
                    }
                    nodes.append(concept_node)
                    
                    edge = {
                        'from': f"a_{article.id}",
                        'to': f"c_{ac.concept.id}",
                        'label': 'MENTIONS',
                        'confidence': ac.confidence
                    }
                    edges.append(edge)
                
                # 엔티티 노드 및 엣지
                for ae in ArticleEntity.objects.filter(article=article):
                    entity_node = {
                        'id': f"e_{ae.entity.id}",
                        'label': 'Entity',
                        'name': ae.entity.name,
                        'entity_type': ae.entity.entity_type
                    }
                    nodes.append(entity_node)
                    
                    edge = {
                        'from': f"a_{article.id}",
                        'to': f"e_{ae.entity.id}",
                        'label': 'MENTIONS',
                        'mention_count': ae.mention_count
                    }
                    edges.append(edge)
                
                # 이벤트 노드 및 엣지
                for ae in ArticleEvent.objects.filter(article=article):
                    event_node = {
                        'id': f"ev_{ae.event.id}",
                        'label': 'Event',
                        'name': ae.event.name,
                        'event_type': ae.event.event_type
                    }
                    nodes.append(event_node)
                    
                    edge = {
                        'from': f"a_{article.id}",
                        'to': f"ev_{ae.event.id}",
                        'label': ae.relationship_type,
                        'confidence': ae.confidence
                    }
                    edges.append(edge)
                
                graph_data = {
                    'nodes': nodes,
                    'edges': edges
                }
            
            return Response(graph_data, status=HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)


class StatusViewSet(viewsets.ReadOnlyModelViewSet):
    """
    status: 상태 체크

    Kibana Heartbeat 상태 체크용 API 입니다.
    """
    permission_classes = [AllowAny, ]
    serializer_class = CaptureSerializer

    def get(self, request, *args, **kwargs):
        return Response(status=HTTP_200_OK)

