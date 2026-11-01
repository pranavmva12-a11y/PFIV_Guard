"""Privacy-minimising helpers for facilitated PFIV Guard usability sessions."""
from __future__ import annotations

SUS_ITEMS = [
    "I think that I would like to use this system frequently.",
    "I found the system unnecessarily complex.",
    "I thought the system was easy to use.",
    "I think that I would need the support of a technical person to be able to use this system.",
    "I found the various functions in this system were well integrated.",
    "I thought there was too much inconsistency in this system.",
    "I would imagine that most people would learn to use this system very quickly.",
    "I found the system very cumbersome to use.",
    "I felt very confident using the system.",
    "I needed to learn a lot of things before I could get going with this system.",
]

USABILITY_TASKS = [
    ("T1", "Analyse a public website URL and identify the detected website purpose."),
    ("T2", "Upload the synthetic checkout screenshot and identify one extracted clue."),
    ("T3", "Decode the synthetic UPI QR and state what the application does not verify."),
    ("T4", "Interpret the ML result and final risk assessment, then state a safe next action."),
]


def score_sus(responses: list[int] | tuple[int, ...]) -> float:
    """Compute the standard SUS score from ten 1..5 Likert responses."""
    if len(responses) != 10:
        raise ValueError("SUS requires exactly 10 responses.")
    if any(not isinstance(value, int) or value < 1 or value > 5 for value in responses):
        raise ValueError("Each SUS response must be an integer from 1 to 5.")
    adjusted = 0
    for index, value in enumerate(responses):
        adjusted += value - 1 if index % 2 == 0 else 5 - value
    return round(adjusted * 2.5, 2)


def build_participant_record(
    participant_code: str,
    task_results: list[dict],
    sus_responses: list[int],
    comments: str = "",
) -> dict:
    """Create an anonymous row suitable for CSV export; no personal fields."""
    code = (participant_code or "").strip()
    if not code or len(code) > 20:
        raise ValueError("Use a short anonymous participant code (1-20 characters).")
    if len(task_results) != len(USABILITY_TASKS):
        raise ValueError("Four task records are required.")
    record = {
        "Participant_Code": code,
        "SUS_Score": score_sus(sus_responses),
        "Task_Success_Count": sum(bool(item.get("completed")) for item in task_results),
        "Task_Count": len(USABILITY_TASKS),
        "Total_Errors": sum(max(0, int(item.get("errors", 0))) for item in task_results),
        "Total_Help_Requests": sum(bool(item.get("help_needed")) for item in task_results),
        "Comments": (comments or "").strip()[:1000],
    }
    for (task_code, _label), item in zip(USABILITY_TASKS, task_results):
        record[f"{task_code}_Completed"] = bool(item.get("completed"))
        record[f"{task_code}_Time_Seconds"] = max(0.0, float(item.get("time_seconds", 0)))
        record[f"{task_code}_Errors"] = max(0, int(item.get("errors", 0)))
        record[f"{task_code}_Help_Needed"] = bool(item.get("help_needed"))
    for index, value in enumerate(sus_responses, start=1):
        record[f"SUS_Q{index}"] = int(value)
    return record
