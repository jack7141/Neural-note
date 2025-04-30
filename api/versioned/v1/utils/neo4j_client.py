from py2neo import Graph, Node, Relationship
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Neo4jClient:
    """Neo4j 그래프 데이터베이스 클라이언트"""
    
    def __init__(self):
        """Neo4j 연결 초기화"""
        try:
            # 명시적으로 URI, 사용자 이름, 비밀번호 로그 출력 (디버깅용)
            logger.info(f"Neo4j 연결 시도: {settings.NEO4J_URI}")
            
            # Neo4j AuraDB의 경우 인증서 검증을 건너뛰도록 설정
            self.graph = Graph(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                secure=True,
                verify=True
            )
            logger.info("Neo4j 연결 성공")
        except Exception as e:
            logger.error(f"Neo4j 연결 실패: {str(e)}")
            self.graph = None
    
    def create_article_node(self, article):
        """기사 노드 생성"""
        if not self.graph:
            logger.error("Neo4j 연결이 없습니다.")
            return None
        
        try:
            query = """
            MERGE (a:Article {id: $article_id})
            SET a.title = $title, 
                a.url = $url, 
                a.created_at = $created_at,
                a.source = $source
            RETURN a
            """
            
            result = self.graph.run(
                query, 
                article_id=article.id, 
                title=article.title, 
                url=article.url,
                created_at=str(article.created_at),
                source=article.source
            )
            
            return result.evaluate()
        except Exception as e:
            logger.error(f"기사 노드 생성 실패: {str(e)}")
            return None
    
    def create_concept_node(self, concept):
        """개념 노드 생성"""
        if not self.graph:
            logger.error("Neo4j 연결이 없습니다.")
            return None
        
        try:
            query = """
            MERGE (c:Concept {id: $concept_id})
            SET c.name = $name, 
                c.description = $description,
                c.confidence = $confidence
            RETURN c
            """
            
            result = self.graph.run(
                query, 
                concept_id=concept.id, 
                name=concept.name, 
                description=concept.description,
                confidence=concept.confidence
            )
            
            return result.evaluate()
        except Exception as e:
            logger.error(f"개념 노드 생성 실패: {str(e)}")
            return None
    
    def create_entity_node(self, entity):
        """엔티티 노드 생성"""
        if not self.graph:
            logger.error("Neo4j 연결이 없습니다.")
            return None
        
        try:
            query = """
            MERGE (e:Entity {id: $entity_id})
            SET e.name = $name, 
                e.entity_type = $entity_type,
                e.description = $description
            RETURN e
            """
            
            result = self.graph.run(
                query, 
                entity_id=entity.id, 
                name=entity.name, 
                entity_type=entity.entity_type,
                description=entity.description
            )
            
            return result.evaluate()
        except Exception as e:
            logger.error(f"엔티티 노드 생성 실패: {str(e)}")
            return None
    
    def create_event_node(self, event):
        """이벤트 노드 생성"""
        if not self.graph:
            logger.error("Neo4j 연결이 없습니다.")
            return None
        
        try:
            query = """
            MERGE (e:Event {id: $event_id})
            SET e.name = $name, 
                e.description = $description,
                e.event_date = $event_date,
                e.event_type = $event_type
            RETURN e
            """
            
            result = self.graph.run(
                query, 
                event_id=event.id, 
                name=event.name, 
                description=event.description,
                event_date=str(event.event_date) if event.event_date else None,
                event_type=event.event_type
            )
            
            return result.evaluate()
        except Exception as e:
            logger.error(f"이벤트 노드 생성 실패: {str(e)}")
            return None
    
    def create_article_concept_relationship(self, article_concept):
        """기사와 개념 간의 관계 생성"""
        if not self.graph:
            logger.error("Neo4j 연결이 없습니다.")
            return None
        
        try:
            query = """
            MATCH (a:Article {id: $article_id})
            MATCH (c:Concept {id: $concept_id})
            MERGE (a)-[r:MENTIONS {confidence: $confidence, is_key_concept: $is_key_concept}]->(c)
            RETURN r
            """
            
            result = self.graph.run(
                query, 
                article_id=article_concept.article.id, 
                concept_id=article_concept.concept.id,
                confidence=article_concept.confidence,
                is_key_concept=article_concept.is_key_concept
            )
            
            return result.evaluate()
        except Exception as e:
            logger.error(f"기사-개념 관계 생성 실패: {str(e)}")
            return None
    
    def create_article_entity_relationship(self, article_entity):
        """기사와 엔티티 간의 관계 생성"""
        if not self.graph:
            logger.error("Neo4j 연결이 없습니다.")
            return None
        
        try:
            query = """
            MATCH (a:Article {id: $article_id})
            MATCH (e:Entity {id: $entity_id})
            MERGE (a)-[r:MENTIONS {confidence: $confidence, mention_count: $mention_count}]->(e)
            RETURN r
            """
            
            result = self.graph.run(
                query, 
                article_id=article_entity.article.id, 
                entity_id=article_entity.entity.id,
                confidence=article_entity.confidence,
                mention_count=article_entity.mention_count
            )
            
            return result.evaluate()
        except Exception as e:
            logger.error(f"기사-엔티티 관계 생성 실패: {str(e)}")
            return None
    
    def create_article_event_relationship(self, article_event):
        """기사와 이벤트 간의 관계 생성"""
        if not self.graph:
            logger.error("Neo4j 연결이 없습니다.")
            return None
        
        try:
            query = f"""
            MATCH (a:Article {{id: $article_id}})
            MATCH (e:Event {{id: $event_id}})
            MERGE (a)-[r:{article_event.relationship_type} {{confidence: $confidence}}]->(e)
            RETURN r
            """
            
            result = self.graph.run(
                query, 
                article_id=article_event.article.id, 
                event_id=article_event.event.id,
                confidence=article_event.confidence
            )
            
            return result.evaluate()
        except Exception as e:
            logger.error(f"기사-이벤트 관계 생성 실패: {str(e)}")
            return None
    
    def create_article_relationship(self, article_relationship):
        """기사 간의 관계 생성"""
        if not self.graph:
            logger.error("Neo4j 연결이 없습니다.")
            return None
        
        try:
            query = f"""
            MATCH (a1:Article {{id: $source_id}})
            MATCH (a2:Article {{id: $target_id}})
            MERGE (a1)-[r:{article_relationship.relationship_type} {{similarity_score: $similarity_score}}]->(a2)
            RETURN r
            """
            
            result = self.graph.run(
                query, 
                source_id=article_relationship.source_article.id, 
                target_id=article_relationship.target_article.id,
                similarity_score=article_relationship.similarity_score
            )
            
            return result.evaluate()
        except Exception as e:
            logger.error(f"기사-기사 관계 생성 실패: {str(e)}")
            return None
    
    def create_concept_relationship(self, concept_relationship):
        """개념 간의 관계 생성"""
        if not self.graph:
            logger.error("Neo4j 연결이 없습니다.")
            return None
        
        try:
            query = f"""
            MATCH (c1:Concept {{id: $source_id}})
            MATCH (c2:Concept {{id: $target_id}})
            MERGE (c1)-[r:{concept_relationship.relationship_type} {{weight: $weight}}]->(c2)
            RETURN r
            """
            
            result = self.graph.run(
                query, 
                source_id=concept_relationship.source_concept.id, 
                target_id=concept_relationship.target_concept.id,
                weight=concept_relationship.weight
            )
            
            return result.evaluate()
        except Exception as e:
            logger.error(f"개념-개념 관계 생성 실패: {str(e)}")
            return None
    
    def find_similar_articles(self, article_id, limit=5):
        """유사한 기사 찾기"""
        if not self.graph:
            logger.error("Neo4j 연결이 없습니다.")
            return []
        
        try:
            # 같은 이벤트를 다루는 기사 찾기
            query = """
            MATCH (a1:Article {id: $article_id})-[]->(e:Event)<-[]-(a2:Article)
            WHERE a1 <> a2
            RETURN a2.id AS article_id, a2.title AS title, COUNT(e) AS common_events
            ORDER BY common_events DESC
            LIMIT $limit
            """
            
            results = self.graph.run(
                query, 
                article_id=article_id,
                limit=limit
            )
            
            return [dict(record) for record in results]
        except Exception as e:
            logger.error(f"유사 기사 검색 실패: {str(e)}")
            return []
    
    def find_related_concepts(self, concept_name, limit=10):
        """관련 개념 찾기"""
        if not self.graph:
            logger.error("Neo4j 연결이 없습니다.")
            return []
        
        try:
            query = """
            MATCH (c1:Concept {name: $concept_name})-[r]-(c2:Concept)
            RETURN c2.name AS name, c2.description AS description, TYPE(r) AS relationship_type, r.weight AS weight
            ORDER BY r.weight DESC
            LIMIT $limit
            """
            
            results = self.graph.run(
                query, 
                concept_name=concept_name,
                limit=limit
            )
            
            return [dict(record) for record in results]
        except Exception as e:
            logger.error(f"관련 개념 검색 실패: {str(e)}")
            return []
    
    def get_article_knowledge_graph(self, article_id):
        """기사의 지식 그래프 가져오기"""
        if not self.graph:
            logger.error("Neo4j 연결이 없습니다.")
            return None
        
        try:
            query = """
            MATCH (a:Article {id: $article_id})-[r1]->(n)
            OPTIONAL MATCH (n)-[r2]->(m)
            WHERE n:Concept OR n:Entity OR n:Event
            RETURN a, r1, n, r2, m
            LIMIT 100
            """
            
            results = self.graph.run(
                query, 
                article_id=article_id
            )
            
            # 결과를 그래프 형태로 가공
            nodes = []
            edges = []
            
            for record in results:
                # 노드 추가
                for node in [record.get("a"), record.get("n"), record.get("m")]:
                    if node and node not in nodes:
                        nodes.append(node)
                
                # 엣지 추가
                if record.get("r1"):
                    edges.append({
                        "from": record.get("a").identity,
                        "to": record.get("n").identity,
                        "type": type(record.get("r1")).__name__,
                        "properties": dict(record.get("r1"))
                    })
                
                if record.get("r2"):
                    edges.append({
                        "from": record.get("n").identity,
                        "to": record.get("m").identity,
                        "type": type(record.get("r2")).__name__,
                        "properties": dict(record.get("r2"))
                    })
            
            return {
                "nodes": [{"id": node.identity, "labels": list(node.labels), "properties": dict(node)} for node in nodes if node],
                "edges": edges
            }
        except Exception as e:
            logger.error(f"기사 지식 그래프 검색 실패: {str(e)}")
            return None 