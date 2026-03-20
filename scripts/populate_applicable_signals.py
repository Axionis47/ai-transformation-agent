"""Populate applicable_signals for all victories in victories.json."""

import json, os

PATH = os.path.join(os.path.dirname(__file__), "../tests/fixtures/rag_seeds/victories.json")

# (signal_type, keywords_to_match_in_victory_text)
RULES = [
    ("tech_stack",    ["api", "rest", "cloud", "aws", "gcp", "azure", "saas", "erp", "tms", "ehr", "legacy system", "integration", "docker", "database"]),
    ("data_signal",   ["months of data", "years of data", "history", "data pipeline", "telemetry", "stream", "bigquery", "feature store", "ingest", "etl"]),
    ("ml_signal",     ["xgboost", "lightgbm", "gradient boost", "random forest", "neural", "bert", "llm", "classifier", "regression", "fine-tun", "machine learning", "nlp", "computer vision", "prediction", "auc"]),
    ("intent_signal", ["no tooling", "no intelligence layer", "no early warning", "leaving for competitors", "no ml capability", "manual process"]),
    ("ops_signal",    ["deployed as", "real-time", "retraining", "monitoring", "model serving", "cloud run", "sagemaker", "vertex ai", "redis", "pubsub", "on-premise"]),
    ("industry_hint", ["industry", "sector", "logistics", "healthcare", "financial", "retail", "manufacturing", "insurance", "energy", "real estate", "construction", "ecommerce", "consultancy", "consulting", "bank", "lender"]),
    ("scale_hint",    ["employees", "revenue", "enterprise", "mid-market", "startup", "annual", "volume", "transactions per", "visits", "discharges", "clients", "accounts"]),
    ("process_signal",["manual", "spreadsheet", "paper", "legacy", "rules", "exception", "workflow", "review", "dispatch", "underwriter", "analyst", "scheduling", "searching", "drafting", "triag"]),
    ("hiring_signal", ["fte", "staff", "team capacity", "headcount", "redeployed", "recaptured", "freed"]),
    ("pain_point",    ["cost", "loss", "penalty", "churn", "delay", "spoilage", "fraud", "default", "denial", "inefficien", "backlog", "late delivery", "false positive"]),
]


def _text(v):
    tech = v.get("tech_stack", {})
    parts = [v.get("problem_statement",""), v.get("solution_summary",""), v.get("embed_text","")]
    if isinstance(tech, dict):
        parts += tech.get("data_sources", []) + [tech.get("ml_approach","")]
        parts += tech.get("infrastructure", [])
    return " ".join(parts).lower()


def derive_signals(v):
    text = _text(v)
    return [sig for sig, kws in RULES if any(k in text for k in kws)]


def main():
    with open(PATH) as f:
        victories = json.load(f)
    for v in victories:
        v["applicable_signals"] = derive_signals(v)
    with open(PATH, "w") as f:
        json.dump(victories, f, indent=2)
    empty = [v["id"] for v in victories if not v["applicable_signals"]]
    print(f"Updated {len(victories)} victories. Empty: {empty or 'none'}")


if __name__ == "__main__":
    main()
