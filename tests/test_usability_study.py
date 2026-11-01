import pytest
from usability_study import score_sus, build_participant_record, USABILITY_TASKS


def test_sus_maximum_score_from_favourable_pattern():
    assert score_sus([5, 1, 5, 1, 5, 1, 5, 1, 5, 1]) == 100.0


def test_sus_minimum_score_from_unfavourable_pattern():
    assert score_sus([1, 5, 1, 5, 1, 5, 1, 5, 1, 5]) == 0.0


def test_sus_rejects_wrong_count_and_values():
    with pytest.raises(ValueError):
        score_sus([3] * 9)
    with pytest.raises(ValueError):
        score_sus([0] + [3] * 9)


def test_anonymous_record_has_no_name_or_email_fields():
    tasks = [
        {"completed": True, "time_seconds": 12, "errors": 0, "help_needed": False}
        for _ in USABILITY_TASKS
    ]
    row = build_participant_record("P01", tasks, [3] * 10)
    assert row["SUS_Score"] == 50.0
    assert row["Task_Success_Count"] == 4
    assert "Name" not in row and "Email" not in row


def test_participant_code_is_required():
    with pytest.raises(ValueError):
        build_participant_record("", [], [3] * 10)
