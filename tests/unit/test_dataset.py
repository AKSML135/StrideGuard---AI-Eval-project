import pytest
from pydantic import ValidationError

from strideguard.models import GoldenCase
from strideguard.datasets import validate_case_ids

# --- TEST 1: From the instruction image ---
def test_case_id_must_be_stable_machine_readable() -> None:
    with pytest.raises(ValidationError):
        GoldenCase.model_validate(
            {
                "case_id": "CASE", # Invalid ID format (spaces, lowercase)
                "description": "invalid ID",
                "user_input": "change it",
                "expected_behavior": {},
            }
        )

# --- TEST 2: Deliberate Failure Exercise (Duplicate ID Check) ---
def test_deliberate_failure_duplicate_case_ids() -> None:
    # Create two valid records that share the SAME case_id
    case_1 = GoldenCase.model_validate(
        {
            "case_id": "CASE_001",
            "description": "First case",
            "user_input": "change it",
            "expected_behavior": {},
        }
    )
    case_2 = GoldenCase.model_validate(
        {
            "case_id": "CASE_001",  # Changed to match case_1 perfectly
            "description": "Second case",
            "user_input": "change it again",
            "expected_behavior": {},
        }
    )

    # validate_case_ids should catch the duplicate and raise a ValueError
    with pytest.raises(ValueError, match="Duplicate case IDs"):
        validate_case_ids([case_1, case_2])