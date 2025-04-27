import os
import django
import sys
from collections import defaultdict

from django.db.models import Q

# Django 설정 로드
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
django.setup()

from connection.models import Connection
from knowledgesnode.models import Concept, Content, ContentAnalysis

# 상관도 임계값 설정
threshold = 0.8

# 콘텐츠별 개념 매핑을 위한 딕셔너리 생성
content_concepts = defaultdict(list)

# 모든 개념을 가져와서 콘텐츠별로 분류
for concept in Concept.objects.all():
    content_title = concept.content_analysis.content.title
    content_concepts[content_title].append(concept)

# 콘텐츠별 강한 연결 정보 출력
print("\n콘텐츠별 강한 연결 정보:")
print("=" * 100)

for content_title, concepts in content_concepts.items():
    # 이 콘텐츠에서 추출된 개념들의 ID 목록
    concept_ids = [c.id for c in concepts]

    # 이 콘텐츠의 개념들이 가진 강한 연결 찾기
    strong_connections = Connection.objects.filter(
        (Q(source__id__in=concept_ids) | Q(target__id__in=concept_ids)) &
        Q(strength__gte=threshold)
    ).distinct()

    if strong_connections.exists():
        print(f"\n콘텐츠: {content_title}")
        print("-" * 100)
        print(f"{'개념 1':<30} | {'개념 2':<30} | {'강도':<10}")
        print("-" * 100)


        # 해당 콘텐츠에 속한 개념들만 필터링하는 함수
        def is_internal(concept):
            return concept.id in concept_ids


        # 내부 연결과 외부 연결 분리
        internal_connections = []
        external_connections = []

        for conn in strong_connections:
            source_internal = is_internal(conn.source)
            target_internal = is_internal(conn.target)

            # 둘 다 내부 개념인 경우
            if source_internal and target_internal:
                internal_connections.append((conn.source.name, conn.target.name, conn.strength))
            # 하나만 내부 개념인 경우
            elif source_internal or target_internal:
                internal_concept = conn.source if source_internal else conn.target
                external_concept = conn.target if source_internal else conn.source
                external_connections.append((internal_concept.name, external_concept.name, conn.strength))

        # 내부 연결 출력
        if internal_connections:
            print("\n[내부 연결 - 동일 콘텐츠 내 개념 간 연결]")
            for src, tgt, strength in sorted(internal_connections, key=lambda x: x[2], reverse=True):
                print(f"{src:<30} | {tgt:<30} | {strength:.4f}")

        # 외부 연결 출력
        if external_connections:
            print("\n[외부 연결 - 다른 콘텐츠의 개념과의 연결]")
            for internal, external, strength in sorted(external_connections, key=lambda x: x[2], reverse=True):
                print(f"{internal:<30} | {external:<30} | {strength:.4f}")

# 콘텐츠 간 연결 요약
print("\n\n콘텐츠 간 강한 연결 요약:")
print("=" * 100)

# 모든 콘텐츠 가져오기
all_contents = Content.objects.all()
content_pairs = []

# 콘텐츠 쌍별로 강한 연결 개수 계산
for i, content1 in enumerate(all_contents):
    content1_concepts = set(Concept.objects.filter(content_analysis__content=content1).values_list('id', flat=True))

    for content2 in all_contents[i + 1:]:
        content2_concepts = set(Concept.objects.filter(content_analysis__content=content2).values_list('id', flat=True))

        # 두 콘텐츠 간 강한 연결 찾기
        cross_connections = Connection.objects.filter(
            (Q(source__id__in=content1_concepts) & Q(target__id__in=content2_concepts)) |
            (Q(source__id__in=content2_concepts) & Q(target__id__in=content1_concepts)),
            strength__gte=threshold
        ).count()

        if cross_connections > 0:
            content_pairs.append((content1.title, content2.title, cross_connections))

# 연결 개수 기준으로 정렬
content_pairs.sort(key=lambda x: x[2], reverse=True)

# 상위 연결 콘텐츠 쌍 출력
print(f"{'콘텐츠 1':<40} | {'콘텐츠 2':<40} | {'강한 연결 수'}")
print("-" * 100)

for content1, content2, count in content_pairs[:20]:  # 상위 20개만 표시
    print(f"{content1[:39]:<40} | {content2[:39]:<40} | {count}")

print("\n스크립트 실행 완료!")