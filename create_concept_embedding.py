import os
import sys
import django
import numpy as np
import time

from django.db.models import Q

# Django 설정 로드
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
django.setup()

from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity
from knowledgesnode.models import Concept
from connection.models import Connection

print('개념 임베딩 및 연결 테스트 시작')

# OpenAI API 키 설정
OPENAI_API_KEY = "SECRET"
if not OPENAI_API_KEY:
    print('오류: OpenAI API 키가 설정되지 않았습니다. 환경 변수 OPENAI_API_KEY를 설정해주세요.')
    sys.exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)

# 기존 개념 가져오기
concepts = Concept.objects.all()
concept_count = concepts.count()

if concept_count == 0:
    print('테스트할 개념이 없습니다. 먼저 데이터를 추가해주세요.')
    sys.exit(1)

print(f'총 {concept_count}개 개념에 대해 임베딩을 생성합니다.')

# 임베딩 생성 및 저장
updated_concepts = []
for i, concept in enumerate(concepts):
    print(f'[{i + 1}/{concept_count}] 개념 "{concept.name}" 처리 중...')

    # 이미 임베딩이 있는지 확인
    if concept.vector_embedding:
        print(f'✓ 이미 임베딩이 존재합니다: {concept.name}')
        continue

    try:
        # OpenAI API로 임베딩 생성
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=concept.name
        )

        # 임베딩 저장
        embedding = response.data[0].embedding
        concept.vector_embedding = embedding
        updated_concepts.append(concept)

        print(f'✓ 임베딩 생성 완료: {concept.name}')

    except Exception as e:
        print(f'✗ 임베딩 생성 실패: {concept.name}, 오류: {str(e)}')

    # API 요청 사이에 잠시 대기 (초당 요청 제한 고려)
    time.sleep(0.5)

# 벌크 업데이트
if updated_concepts:
    Concept.objects.bulk_update(updated_concepts, ['vector_embedding'])
    print(f'{len(updated_concepts)}개 개념의 임베딩 저장 완료')
else:
    print('업데이트할 임베딩이 없습니다.')

# 유사도 계산 및 연결 생성
print('\n개념 간 유사도 계산 및 연결 생성 중...')

# 기존 연결 수 확인
initial_connection_count = Connection.objects.count()
print(f'기존 연결: {initial_connection_count}개')

# 새 연결 생성
new_connections = []
processed_pairs = set()  # 이미 처리한 쌍 추적

threshold = 0.7  # 유사도 임계값
concepts_with_embedding = Concept.objects.exclude(vector_embedding=None)
concept_list = list(concepts_with_embedding)

for i, concept1 in enumerate(concept_list):
    vec1 = np.array(concept1.vector_embedding)

    for j in range(i + 1, len(concept_list)):
        concept2 = concept_list[j]

        # 이미 연결이 있는지 확인
        existing_connection = Connection.objects.filter(
            (Q(source=concept1) & Q(target=concept2)) |
            (Q(source=concept2) & Q(target=concept1))
        ).exists()

        if existing_connection:
            continue

        # 유사도 계산
        vec2 = np.array(concept2.vector_embedding)
        similarity = cosine_similarity([vec1], [vec2])[0][0]

        # 임계값 이상인 경우 연결 생성
        if similarity >= threshold:
            connection = Connection(
                source=concept1,
                target=concept2,
                strength=float(similarity)
            )
            new_connections.append(connection)

            print(f'새 연결: {concept1.name} ↔ {concept2.name} (유사도: {similarity:.4f})')

# 연결 벌크 생성
if new_connections:
    Connection.objects.bulk_create(new_connections)
    print(f'{len(new_connections)}개의 새 연결 생성 완료')
else:
    print('임계값을 넘는 새 연결이 없습니다.')

# 결과 요약
final_connection_count = Connection.objects.count()
new_added = final_connection_count - initial_connection_count

print('\n===== 처리 결과 요약 =====')
print(f'처리된 개념: {len(updated_concepts)}/{concept_count}')
print(f'생성된 새 연결: {new_added}개')
print(f'총 연결: {final_connection_count}개')

# 연결 강도별 분포 출력
if final_connection_count > 0:
    print('\n연결 강도 분포:')
    for range_start in [0.9, 0.8, 0.7]:
        count = Connection.objects.filter(
            strength__gte=range_start,
            strength__lt=range_start + 0.1
        ).count()
        print(f'{range_start} ~ {range_start + 0.1}: {count}개')

print('\n임베딩 및 연결 생성 완료!')