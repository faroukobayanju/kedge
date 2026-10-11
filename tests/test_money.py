import json

from kedge import money

PRICING = {"price_per_green_usd": 10, "target_gross_margin": 0.925, "payment_fee_rate": 0.03}


def test_model_budget_comes_from_the_cfo_model():
    # $10 price, 92.5% margin -> $0.75 total cost allowed, minus $0.30 payment fee -> $0.45 for the model
    assert money.model_budget(PRICING) == 0.45


def test_predict_uses_recent_step_costs():
    assert money.predict([]) == 0.0
    assert money.predict([0.1, 0.2, 0.3, 0.6]) == round((0.2 + 0.3 + 0.6) / 3, 4)


def test_margin_line():
    line = money.margin_line(0.38, PRICING)
    assert "$0.38" in line and "$10" in line and "93.2%" in line


def test_meter_only_for_litellm(monkeypatch):
    monkeypatch.setenv("KEDGE_MODEL", "opencode/big-pickle")
    monkeypatch.setenv("LITELLM_API_KEY", "x")
    assert money.Meter().read() is None


def test_meter_reads_key_spend(monkeypatch):
    monkeypatch.setenv("KEDGE_MODEL", "litellm/claude-haiku")
    monkeypatch.setenv("LITELLM_API_KEY", "x")
    monkeypatch.setattr(money, "_key_info", lambda key: {"info": {"spend": 1.25}})
    assert money.Meter().read() == 1.25


def test_meter_survives_network_errors(monkeypatch):
    monkeypatch.setenv("KEDGE_MODEL", "litellm/claude-haiku")
    monkeypatch.setenv("LITELLM_API_KEY", "x")

    def boom(key):
        raise OSError("down")
    monkeypatch.setattr(money, "_key_info", boom)
    assert money.Meter().read() is None


def test_ledger_appends_csv(tmp_path):
    p = tmp_path / "ledger.csv"
    money.ledger_append(str(p), {"run_id": "r1", "status": "green", "real_cost_usd": 0.38})
    money.ledger_append(str(p), {"run_id": "r2", "status": "gave_up", "real_cost_usd": 0.2})
    lines = p.read_text().splitlines()
    assert lines[0].startswith("run_id,") and len(lines) == 3


def test_load_pricing_file(tmp_path):
    p = tmp_path / "pricing.json"
    p.write_text(json.dumps(PRICING))
    assert money.load_pricing(str(p))["price_per_green_usd"] == 10
