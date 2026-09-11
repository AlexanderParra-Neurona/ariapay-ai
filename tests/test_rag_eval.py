import asyncio
import inspect
import json
from pathlib import Path
from typing import Any

import pytest
from ragas.metrics.collections.base import BaseMetric

from app.routers.v1.chat import _answer_from_docs
from app.services.eval import get_ragas_metrics
from app.services.retrieval import get_hybrid_retriever

EVAL_SET_PATH = Path(__file__).parent / "fixtures" / "eval_set.json"
METRIC_THRESHOLD = 0.5


def _load_eval_set() -> list[dict[str, str]]:
    return json.loads(EVAL_SET_PATH.read_text())


async def _score_sample(
    metric: BaseMetric,
    user_input: str,
    response: str,
    retrieved_contexts: list[str],
    reference: str,
) -> float:
    params = inspect.signature(metric.ascore).parameters
    kwargs: dict[str, Any] = {}
    if "user_input" in params:
        kwargs["user_input"] = user_input
    if "response" in params:
        kwargs["response"] = response
    if "retrieved_contexts" in params:
        kwargs["retrieved_contexts"] = retrieved_contexts
    if "reference" in params:
        kwargs["reference"] = reference
    result = await metric.ascore(**kwargs)
    return result.value


def _build_sample(item: dict[str, str]) -> dict[str, Any]:
    query, reference = item["query"], item["reference"]
    answer, _citations, _confidence, _short_circuit = _answer_from_docs(query)
    hits = get_hybrid_retriever().search(query)
    contexts = [doc.page_content for doc, _score in hits]
    return {
        "user_input": query,
        "response": answer,
        "retrieved_contexts": contexts,
        "reference": reference,
    }


@pytest.fixture(scope="module")
def eval_set() -> list[dict[str, str]]:
    return _load_eval_set()


@pytest.fixture(scope="module")
def ragas_metrics() -> list[BaseMetric]:
    return get_ragas_metrics()


@pytest.fixture(scope="module")
def eval_scores(
    eval_set: list[dict[str, str]], ragas_metrics: list[BaseMetric]
) -> list[dict[str, float]]:
    rows = []
    for item in eval_set:
        sample = _build_sample(item)
        row = {
            metric.name: asyncio.run(_score_sample(metric, **sample))
            for metric in ragas_metrics
        }
        rows.append(row)
    return rows


@pytest.mark.eval
@pytest.mark.parametrize(
    "index", range(len(_load_eval_set())), ids=lambda i: _load_eval_set()[i]["query"]
)
def test_rag_answer_meets_quality_thresholds(
    index: int, eval_scores: list[dict[str, float]]
) -> None:
    row = eval_scores[index]
    failures = {
        name: score for name, score in row.items() if score < METRIC_THRESHOLD
    }
    assert not failures, f"metrics below {METRIC_THRESHOLD}: {failures}"


@pytest.mark.eval
def test_rag_eval_summary(eval_scores: list[dict[str, float]]) -> None:
    metric_names = eval_scores[0].keys()
    means = {
        name: sum(row[name] for row in eval_scores) / len(eval_scores)
        for name in metric_names
    }
    print("\nRAG eval summary (mean across eval set):")
    for name, mean in means.items():
        print(f"  {name}: {mean:.3f}")
