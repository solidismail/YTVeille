"""
Mots-clés techniques Kubernetes pour le scoring sémantique.
Organisés par thème / topic.
"""
from typing import Dict, List

TOPIC_KEYWORDS: Dict[str, List[str]] = {
    "incident": [
        "incident", "post-mortem", "postmortem", "panne", "outage",
        "crash", "debug", "root cause", "rca", "blameless",
    ],
    "architecture": [
        "architecture", "diagram", "schema", "multi-cluster", "multi cluster",
        "federation", "service mesh", "sidecar", "istio", "linkerd",
    ],
    "observabilité": [
        "prometheus", "grafana", "alertmanager", "loki", "tracing",
        "jaeger", "opentelemetry", "metrics", "slo", "sla", "sli",
        "observabilité", "monitoring", "dashboards",
    ],
    "sécurité": [
        "rbac", "pod security", "opa", "gatekeeper", "falco",
        "network policy", "secret", "vault", "trivy", "kubescape",
    ],
    "ci_cd": [
        "argocd", "argo cd", "flux", "fluxcd", "helm", "kustomize",
        "gitops", "pipeline", "ci/cd", "tekton", "jenkins",
    ],
    "scaling": [
        "hpa", "vpa", "keda", "scalabilité", "scaling", "autoscaling",
        "horizontal", "vertical", "cluster autoscaler", "cost",
    ],
    "migration": [
        "migration", "upgrade", "mise à jour", "version", "deprecation",
        "zero downtime", "rolling update", "canary", "blue green",
    ],
    "storage": [
        "pvc", "persistent volume", "csi", "storage class", "statefulset",
        "rook", "ceph", "nfs", "longhorn", "backup", "velero",
    ],
}

# Liste plate pour détection rapide
ALL_KEYWORDS: List[str] = [kw for kws in TOPIC_KEYWORDS.values() for kw in kws]

# Mots-clés avancés (bonus score élevé)
ADVANCED_KEYWORDS: List[str] = [
    "post-mortem", "postmortem", "root cause", "blameless",
    "service mesh", "istio", "linkerd", "opentelemetry",
    "rbac", "opa", "gatekeeper", "falco",
    "argocd", "gitops", "keda", "hpa",
    "multi-cluster", "federation", "zero downtime",
    "slo", "sla", "sli", "cluster autoscaler",
]
