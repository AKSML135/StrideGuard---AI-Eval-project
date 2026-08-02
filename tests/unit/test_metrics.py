from strideguard.metrics import exact_agreement


def test_human_agreement_metrics() -> None:
    a = ["pass", "fail", "pass", "fail"]
    b = ["pass", "fail", "fail", "fail"]

    assert exact_agreement(a, b) == 0.75
