from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from api.versioned.v1.concept.serializers import ConceptSerializer
from api.versioned.v1.utils.neo4j_client import Neo4jClient
from concept.models import Concept, ConceptRelationship, ConceptDomain
from event.models import Event
from entity.models import Entity
from entity import models

class ConceptViewSet(viewsets.ModelViewSet):
    """
    개념 API
    
    개념 조회, 관리를 위한 API입니다.
    """
    permission_classes = [IsAuthenticated, ]
    serializer_class = ConceptSerializer
    queryset = Concept.objects.all()
    
    @action(detail=True, methods=['get'])
    def related_concepts(self, request, pk=None):
        """관련 개념 조회"""
        try:
            concept = self.get_object()
            
            # 관련 개념 조회 (Django ORM)
            related = ConceptRelationship.objects.filter(source_concept=concept)
            
            result = []
            for rel in related:
                result.append({
                    'concept_id': rel.target_concept.id,
                    'name': rel.target_concept.name,
                    'description': rel.target_concept.description,
                    'relationship_type': rel.relationship_type,
                    'weight': rel.weight
                })
            
            # Neo4j에서 추가 관련 개념 조회
            neo4j_client = Neo4jClient()
            neo4j_related = neo4j_client.find_related_concepts(concept.name)
            
            # 중복 제거하면서 Neo4j 결과 추가
            existing_names = [item['name'] for item in result]
            for item in neo4j_related:
                if item['name'] not in existing_names:
                    result.append({
                        'name': item['name'],
                        'description': item.get('description', ''),
                        'relationship_type': item.get('relationship_type', 'RELATED_TO'),
                        'weight': item.get('weight', 0.5)
                    })
            
            return Response(result, status=HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def domains(self, request):
        """도메인 목록 조회"""
        try:
            domains = ConceptDomain.objects.filter(parent__isnull=True)
            
            result = []
            for domain in domains:
                domain_data = {
                    'id': domain.id,
                    'name': domain.name,
                    'description': domain.description,
                    'children': []
                }
                
                # 하위 도메인 추가
                for child in domain.children.all():
                    domain_data['children'].append({
                        'id': child.id,
                        'name': child.name,
                        'description': child.description
                    })
                
                result.append(domain_data)
            
            return Response(result, status=HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def events(self, request):
        """이벤트 목록 조회"""
        try:
            events = Event.objects.all().order_by('-created_at')
            
            result = []
            for event in events:
                event_data = {
                    'id': event.id,
                    'name': event.name,
                    'description': event.description,
                    'event_date': event.event_date,
                    'event_type': event.event_type,
                    'domain': event.domain.name if event.domain else None,
                    'article_count': event.articles.count()
                }
                
                result.append(event_data)
            
            return Response(result, status=HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def entities(self, request):
        """엔티티 목록 조회"""
        try:
            entity_type = request.query_params.get('type')
            
            if entity_type:
                entities = Entity.objects.filter(entity_type=entity_type)
            else:
                entities = Entity.objects.all()
            
            # 많이 언급된 순으로 정렬
            entities = entities.annotate(
                mention_count=models.Sum('articleentity__mention_count')
            ).order_by('-mention_count')[:100]  # 상위 100개만
            
            result = []
            for entity in entities:
                entity_data = {
                    'id': entity.id,
                    'name': entity.name,
                    'entity_type': entity.entity_type,
                    'description': entity.description,
                    'mention_count': entity.mention_count
                }
                
                result.append(entity_data)
            
            return Response(result, status=HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)
            
    @action(detail=False, methods=['get'])
    def knowledge_graph(self, request):
        """전체 지식 그래프 조회 (제한된 크기)"""
        try:
            # Neo4j에서 지식 그래프 조회
            neo4j_client = Neo4jClient()
            
            # 쿼리 파라미터
            concept_name = request.query_params.get('concept')
            event_name = request.query_params.get('event')
            limit = int(request.query_params.get('limit', 100))
            
            # Cypher 쿼리 구성
            if concept_name:
                query = """
                MATCH (c:Concept {name: $concept_name})-[r1]-(n)
                OPTIONAL MATCH (n)-[r2]-(m)
                WHERE m <> c
                RETURN c, r1, n, r2, m
                LIMIT $limit
                """
                params = {'concept_name': concept_name, 'limit': limit}
                
            elif event_name:
                query = """
                MATCH (e:Event {name: $event_name})-[r1]-(n)
                OPTIONAL MATCH (n)-[r2]-(m)
                WHERE m <> e
                RETURN e, r1, n, r2, m
                LIMIT $limit
                """
                params = {'event_name': event_name, 'limit': limit}
                
            else:
                # 기본 쿼리 - 가장 연결이 많은 상위 노드 중심
                query = """
                MATCH (n)-[r]-(m)
                RETURN n, r, m
                LIMIT $limit
                """
                params = {'limit': limit}
            
            # Neo4j에서 직접 실행
            results = neo4j_client.graph.run(query, **params)
            
            # 결과를 그래프 형태로 가공
            nodes = []
            edges = []
            node_ids = set()
            
            for record in results:
                # 각 레코드의 노드 추출
                record_nodes = [record.get(k) for k in record.keys() if record.get(k) and hasattr(record.get(k), 'identity')]
                
                # 노드 추가 (중복 방지)
                for node in record_nodes:
                    if node and node.identity not in node_ids:
                        node_ids.add(node.identity)
                        nodes.append({
                            'id': node.identity,
                            'labels': list(node.labels),
                            'properties': dict(node)
                        })
                
                # 관계 추출 및 엣지 추가
                for key in record.keys():
                    rel = record.get(key)
                    if rel and hasattr(rel, 'start_node') and hasattr(rel, 'end_node'):
                        edges.append({
                            'from': rel.start_node.identity,
                            'to': rel.end_node.identity,
                            'type': type(rel).__name__,
                            'properties': dict(rel)
                        })
            
            return Response({
                'nodes': nodes,
                'edges': edges
            }, status=HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST) 