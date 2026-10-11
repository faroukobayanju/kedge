"""cfo.ai unit economics as a live guard.

The price per green PR and the target margin come from the cfo.ai model (pricing.json). They set how much
model spend one PR may use. Spend is measured from the LiteLLM key's real bill when the agent runs on a
litellm/* model, because OpenCode's own cost report missed about 3/4 of the real bill in our batch.
"""
import csv
import json
import os
import urllib.request

LITELLM = "https://litellm.vision.aivar.app"
LEDGER_FIELDS = ["run_id", "finished_at", "repo", "pr_url", "status", "model", "real_cost_usd", "steps",
                 "rollbacks", "price_usd", "margin"]


PRICING = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pricing.json")


def load_pricing(path=PRICING) -> dict:
    return json.load(open(path))


def model_budget(p) -> float:
    """What the model may spend on one PR without breaking the cfo.ai margin."""
    price = p["price_per_green_usd"]
    return round(price * (1 - p["target_gross_margin"]) - price * p.get("payment_fee_rate", 0.0), 4)


def predict(step_costs) -> float:
    """Expected cost of the next step: mean of the last three."""
    recent = list(step_costs)[-3:]
    return round(sum(recent) / len(recent), 4) if recent else 0.0


def margin_line(cost, p) -> str:
    price = p["price_per_green_usd"]
    margin = (price - price * p.get("payment_fee_rate", 0.0) - cost) / price
    return (f"This fix cost ${cost:.2f} in model spend. At the cfo.ai price of ${price:g} per green PR "
            f"that leaves a {margin:.1%} gross margin.")


def _key_info(key) -> dict:
    req = urllib.request.Request(f"{LITELLM}/key/info", headers={"Authorization": f"Bearer {key}"})
    return json.load(urllib.request.urlopen(req, timeout=20))


class Meter:
    """Reads the LiteLLM key's total spend. read() is None when the model isn't litellm/* or the API fails."""

    def __init__(self):
        self.key = os.environ.get("LITELLM_API_KEY")
        self.on = bool(self.key) and os.environ.get("KEDGE_MODEL", "").startswith("litellm/")

    def read(self) -> float | None:
        if not self.on:
            return None
        try:
            return float(_key_info(self.key)["info"]["spend"])
        except (OSError, KeyError, ValueError, TypeError):
            return None


def ledger_append(path, row) -> None:
    """One line per run, ready to paste into cfo.ai to refresh the plan with real costs."""
    new = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LEDGER_FIELDS, extrasaction="ignore")
        if new:
            w.writeheader()
        w.writerow(row)
