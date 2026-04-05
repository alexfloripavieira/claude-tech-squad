"""RAGAS-based assessment harness for the RAG pipeline."""
from ragas import evaluate
from ragas.metrics import faithfulness, context_precision


def run_assessment(dataset: list[dict]) -> dict:
    """Assess RAG pipeline output using RAGAS metrics.

    Args:
        dataset: list of {"question": str, "answer": str, "contexts": list[str]}

    Returns:
        dict with faithfulness and context_precision scores.
    """
    result = evaluate(dataset, metrics=[faithfulness, context_precision])
    return {
        "faithfulness": result["faithfulness"],
        "context_precision": result["context_precision"],
    }
