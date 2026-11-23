# Home Services ML engine

One endpoint for the mobile app.

## Run
1. Put `classifier.joblib` (notebook 03) and `price_model.joblib` (notebook 04) in `../models/` (or set the MODELS_DIR environment variable).
2. `pip install -r requirements.txt`
3. `uvicorn app:app --host 0.0.0.0 --port 8000`
4. Interactive docs: http://localhost:8000/docs

## Test page
Open http://localhost:8000/ for a simple page to try phrases and see the result, with a history table you can copy as CSV.

## Request
POST /diagnose
{"text": "kitchen tap is leaking"}

## Responses
Recognised:
{"status": "ok", "trade": "plumber", "group": "tap_mixer", "confidence": 0.77,
 "price": {"currency": "KES", "low": 120, "mid": 260, "high": 580}, "note": "..."}

Not recognised (app shows the three trade tiles instead):
{"status": "unknown", "confidence": 0.14}

Validation errors (empty or missing text) return HTTP 422.

GET /health returns the model in use and the confidence threshold.

## Notes
- Prices are estimates. The range comes from cross-validated error, and the shilling figures use the
  exchange-rate coefficient in price_model.joblib until it is calibrated with real Nairobi quotes.
- To use the latest coefficient or model, rerun notebooks 03 and 04 and restart the server.
