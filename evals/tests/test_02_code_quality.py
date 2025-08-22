import os, json, pathlib, re, importlib.util, sys, hashlib, pytest
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from utils.format_code import folder_to_prompt_string
from pydantic import BaseModel
from typing import cast, List
from utils.prompt import LLM_AS_A_JUDGE_PROMPT, USER_TASK, EXPERT_CODE, BASE_CODE

CANDIDATE_NAME = os.getenv("CANDIDATE_NAME", "openswe").strip()
LLM_AS_JUDGE_MODEL = "claude-sonnet-4-20250514"
CODE_FOLDER = [pathlib.Path("../src/agent")]

# NEW Pydantic model for each evidence item, to include severity
class LlmAsJudgeEvidence(BaseModel):
    issue: str
    severity: str

# UPDATED Pydantic model for the overall output
class LlmAsJudgeOutput(BaseModel):
    codebase_patterns_check: bool
    codebase_patterns_evidence: List[LlmAsJudgeEvidence]
    code_succinctness_check: bool
    code_succinctness_evidence: List[LlmAsJudgeEvidence]
    code_cleanliness_check: bool
    code_cleanliness_evidence: List[LlmAsJudgeEvidence]
    correctness_check: bool
    correctness_evidence: List[LlmAsJudgeEvidence]

def _write_score(score):
    out = pathlib.Path("results"); out.mkdir(parents=True, exist_ok=True)
    with open(out / f"code_quality_{score['candidate']}.json", "w") as f:
        json.dump(score, f, indent=2)

def _add(score, pts, key, ok, msg=""):
    score["details"].append({"key": key, "points": pts, "passed": ok, "msg": msg})
    score["points"] += pts

def _load_judge():
    """
    Returns a (invoke, model_name) tuple.
    Prefers OpenAI via langchain_openai, falls back to Anthropic via langchain_anthropic.
    Skips if neither is importable or no keys.
    """
    llm = ChatAnthropic(model=LLM_AS_JUDGE_MODEL, temperature=0)
    structured_llm = llm.with_structured_output(LlmAsJudgeOutput)

    return (lambda msgs: structured_llm.invoke(msgs)), f"anthropic:{LLM_AS_JUDGE_MODEL}"

def _extract_json(text: str):
    """
    Extract a JSON object from a possibly noisy LLM response.
    Looks for the first {...} block containing the required keys.
    """
    req_keys = {"codebase_patterns_check", "codebase_patterns_evidence", "code_succinctness_check", "code_succinctness_evidence", "code_cleanliness_check", "code_cleanliness_evidence", "correctness_check", "correctness_evidence"}
    try:
        obj = json.loads(text)
        if req_keys.issubset(set(obj.keys())):
            return obj
    except Exception as e:
        raise ValueError(f"Judge did not return parsable JSON with required keys: {e}")

# NEW function to calculate points based on severity
def _calculate_score(evidence_list: List[LlmAsJudgeEvidence], max_points: int) -> int:
    """Calculates a score based on a list of evidence items and their severity."""
    points_deducted = 0
    for evidence in evidence_list:
        if evidence.severity == "critical":
            points_deducted += 2
        elif evidence.severity == "major":
            points_deducted += 1
        elif evidence.severity == "minor":
            points_deducted += 0.5
        else:
            print(f"Warning: Unknown severity level '{evidence.severity}'")
            points_deducted += 1
    
    return max(0, max_points - points_deducted)

def test_best_practices_llm_judge():
    score = {"candidate": CANDIDATE_NAME, "bucket": "code_quality", "points": 0, "max_points": 16, "details": []}
    user_code = folder_to_prompt_string(CODE_FOLDER)
    with open('user_code.txt', 'w') as f:
        f.write(user_code)

    # Prompt the judge with task-specific guidelines
    system = LLM_AS_A_JUDGE_PROMPT.format(user_task=USER_TASK, expert_code=EXPERT_CODE, user_code=user_code, base_code=BASE_CODE)
    user = {
        "role": "user",
        "content": "Return the JSON object evaluating the codebase."
    }

    try:
        invoke, model_name = _load_judge()
        resp = invoke([SystemMessage(content=system), HumanMessage(content=user["content"])])
        judge = cast(LlmAsJudgeOutput, resp)
        print(judge)
        print(judge.codebase_patterns_check)
        print(judge.codebase_patterns_evidence)
        print(judge.code_succinctness_check)
        print(judge.code_succinctness_evidence)
        print(judge.code_cleanliness_check)
        print(judge.code_cleanliness_evidence)
        print(judge.correctness_check)
        print(judge.correctness_evidence)
    except Exception as e:
        _add(score, 0, "judge_error", False, f"Judge error: {type(e).__name__}: {e}")
        _write_score(score)
        pytest.fail(f"LLM judge failed: {e}")

    # SCORING LOGIC - UPDATED TO USE SEVERITY
    
    # Codebase Patterns check
    codebase_patterns_points = _calculate_score(judge.codebase_patterns_evidence, 4)
    _add(score, codebase_patterns_points, "codebase_patterns_check", codebase_patterns_points == 4, str(judge.codebase_patterns_evidence))

    # Code Succinctness check
    code_succinctness_points = _calculate_score(judge.code_succinctness_evidence, 4)
    _add(score, code_succinctness_points, "code_succinctness_check", code_succinctness_points == 4, str(judge.code_succinctness_evidence))

    # Code Cleanliness check
    code_cleanliness_points = _calculate_score(judge.code_cleanliness_evidence, 4)
    _add(score, code_cleanliness_points, "code_cleanliness_check", code_cleanliness_points == 4, str(judge.code_cleanliness_evidence))

    # Correctness check
    correctness_points = _calculate_score(judge.correctness_evidence, 4)
    _add(score, correctness_points, "correctness_check", correctness_points == 4, str(judge.correctness_evidence))

    _write_score(score)