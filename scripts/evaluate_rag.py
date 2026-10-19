"""Retrieval regression benchmark on team-authored samples; no model calls/training."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from uuid import uuid5, NAMESPACE_URL
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.db import SessionLocal
from app.rag_index import retrieve, INDEX_VERSION


def evaluate(db):
    results = []; hits = 0; reciprocal = 0; negative_correct = 0; positives = 0; negatives = 0
    for case in json.loads((ROOT / "fixtures/rag_evaluation.json").read_text(encoding="utf-8")):
        matches, missing = retrieve(db, case["question"])
        ids = [m["document_id"] for m in matches]
        if case["expected"]:
            positives += 1
            expected = str(uuid5(NAMESPACE_URL, "demo-rag-seed:" + case["expected"]))
            success = expected in ids
            if success: hits += 1; reciprocal += 1 / (ids.index(expected) + 1)
        else:
            negatives += 1; success = len(matches) == 0; negative_correct += int(success)
        results.append({**case, "passed": success, "retrieved_ids": ids, "missing_concepts": sorted(missing)})
    return {"at": datetime.now(timezone.utc).isoformat(), "index_method": INDEX_VERSION,
        "dataset": "24 self-authored regression questions over 3 fictional source documents; not an independent/generalisation benchmark",
        "questions": len(results), "positive_questions": positives, "negative_questions": negatives,
        "recall_at_3": hits / positives, "mean_reciprocal_rank_at_3": reciprocal / positives,
        "abstention_accuracy": negative_correct / negatives, "passed": sum(r["passed"] for r in results),
        "actual_model_calls": 0, "results": results}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--evidence", type=Path, default=ROOT / "submission/evidence/rag-retrieval-evaluation.json"); args = parser.parse_args()
    with SessionLocal() as db: result = evaluate(db)
    args.evidence.parent.mkdir(parents=True, exist_ok=True); args.evidence.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k != "results"},ensure_ascii=False))
    if result["passed"] != result["questions"]: raise SystemExit(1)
