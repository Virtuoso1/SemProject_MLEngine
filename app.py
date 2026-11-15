"""Home Services ML engine: one endpoint the mobile app calls.

POST /diagnose  {"text": "kitchen tap is leaking"}
  -> trade, service group, confidence and a KSh price range, or status "unknown".

Run:  uvicorn app:app --host 0.0.0.0 --port 8000
Needs classifier.joblib and price_model.joblib (written by notebooks 03 and 04) in ../models.
"""
import os
import numpy as np
import joblib
from fastapi import FastAPI
from pydantic import BaseModel, Field

# models live in ../models by default; set MODELS_DIR to point somewhere else
MODELS_DIR = os.environ.get("MODELS_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models"))
clf_bundle = joblib.load(os.path.join(MODELS_DIR, "classifier.joblib"))
price_bundle = joblib.load(os.path.join(MODELS_DIR, "price_model.joblib"))

# the multilingual encoder is loaded once, only if a saved model uses it
_encoder = None
def embed(texts, model_name, prefix):
    global _encoder
    if _encoder is None:
        from sentence_transformers import SentenceTransformer
        _encoder = SentenceTransformer(model_name)
    return _encoder.encode([prefix + t for t in texts], normalize_embeddings=True, show_progress_bar=False)

def classify(text):
    b = clf_bundle
    if b["best"] == "embeddings":
        probs = b["clf"].predict_proba(embed([text], b["model_name"], b["prefix"]))[0]
        classes = b["clf"].classes_
    else:
        probs = b["clf"].predict_proba([text])[0]
        classes = b["clf"].classes_
    i = int(np.argmax(probs))
    return str(classes[i]), float(probs[i])

def price_inr(text, group):
    b = price_bundle
    onehot = np.array([[group == g for g in b["groups"]]], dtype=float)
    if b["use_emb"]:
        feats = embed([text.lower()], b["model_name"], b["prefix"])
    else:
        feats = b["tfidf"].transform([text.lower()]).toarray()
    mid = float(np.exp(b["ridge"].predict(np.hstack([feats, onehot]))[0]))
    m = float(np.exp(b["margin"]))
    return mid / m, mid, mid * m

def to_kes(inr_values, group):
    coef = price_bundle["coef"]
    low, mid, high = inr_values
    p = coef.get("power")
    if p:                                     # KSh = a * INR^b, fitted on Nairobi quotes
        mid_kes = p["a"] * mid ** p["b"]
        # range combines the price-model error (scaled by b) and the conversion error
        m = float(np.sqrt((p["b"] * price_bundle["margin"]) ** 2 + p["conv_margin"] ** 2))
        vals = [mid_kes / np.exp(m), mid_kes, mid_kes * np.exp(m)]
    else:
        c = coef.get(price_bundle["trade_of"][group], coef["default"])
        vals = [v * c for v in inr_values]
    return [int(round(v, -1)) for v in vals]

app = FastAPI(title="Home Services ML engine", version="1.0")

class Query(BaseModel):
    text: str = Field(..., min_length=2, max_length=500, description="Customer's description of the problem")

@app.get("/health")
def health():
    return {"status": "ok", "classifier": clf_bundle["best"], "threshold": clf_bundle["threshold"]}

@app.post("/diagnose")
def diagnose(q: Query):
    text = q.text.strip()
    group, conf = classify(text)
    if conf < clf_bundle["threshold"]:
        # app should fall back to showing the trade tiles
        return {"status": "unknown", "confidence": round(conf, 2)}
    low, mid, high = to_kes(price_inr(text, group), group)
    return {
        "status": "ok",
        "trade": clf_bundle["group_to_trade"][group],
        "group": group,
        "confidence": round(conf, 2),
        "price": {"currency": "KES", "low": low, "mid": mid, "high": high},
        "note": "Estimate only. Final price is agreed with the professional.",
    }
