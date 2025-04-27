from django.db import models

from knowledgesnode.models import Concept


class ConceptDomain(models.Model):
    """개념 도메인/주제 분야"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# 미리 정의된 도메인들을 생성하는 마이그레이션 또는 초기화 스크립트
def create_predefined_domains():
    domains = [
        ("통신_네트워크", "통신 기술, 네트워크 인프라, 통신 서비스 관련 주제"),
        ("사이버_보안", "정보 보안, 해킹 방지, 데이터 보호 관련 주제"),
        ("환경_재활용", "환경 보호, 재활용, 지속 가능성 관련 주제"),
        ("IT_기기_가전", "전자기기, 스마트폰, 가전제품 관련 주제"),
        ("에너지_기술", "에너지 생산, 저장, 분배 관련 주제"),
        ("재난_대응", "재난 상황 대처, 구호 활동 관련 주제"),
        ("정책_규제", "정부 정책, 산업 규제, 법률 관련 주제"),
        ("연구개발_혁신", "R&D, 기술 혁신, 연구 활동 관련 주제")
    ]

    for name, desc in domains:
        ConceptDomain.objects.get_or_create(name=name, defaults={"description": desc})


class ConceptCluster(models.Model):
    """유사 개념들의 클러스터"""
    name = models.CharField(max_length=100)
    domain = models.ForeignKey(ConceptDomain, on_delete=models.CASCADE, related_name='clusters')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.domain.name})"

    class Meta:
        unique_together = ['name', 'domain']


class ConceptClusterMembership(models.Model):
    """개념과 클러스터 간의 관계"""
    concept = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name='cluster_memberships')
    cluster = models.ForeignKey(ConceptCluster, on_delete=models.CASCADE, related_name='memberships')
    relevance_score = models.FloatField(default=1.0)  # 클러스터와의 관련성 점수
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['concept', 'cluster']