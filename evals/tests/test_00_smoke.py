# tests/test_00_smoke.py
import importlib.util
import sys
import os
import json
import hashlib
import pathlib
import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

DEFAULT_AGENT_PATH = pathlib.Path.cwd() / "../src/agent/graph.py"
CANDIDATE_NAME = os.getenv("CANDIDATE_NAME", "openswe").strip()


def _load_module(agent_py_path: pathlib.Path):
    """Import agent.py as a temporary module; success == compiles/imports."""
    # Add src directory to Python path so agent package can be imported
    src_path = str(agent_py_path.parent.parent)  # ../src/agent/graph.py -> ../src
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    module_name = "candidate_agent_" + hashlib.md5(str(agent_py_path).encode()).hexdigest()[:8]
    spec = importlib.util.spec_from_file_location(module_name, str(agent_py_path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    try:
        spec.loader.exec_module(mod)
        return mod, None
    except Exception as e:
        return None, f"agent.py must compile/import: {e}"

def _get_app(mod):
    """Return global `graph` or from the module or raise a clear error."""
    if not hasattr(mod, "graph") and not hasattr(mod, "app"):
        raise AssertionError("agent.py must export a global variable `graph` or `app`")
    if hasattr(mod, "graph"):
        return mod.graph
    return mod.app

def _flatten_text(content) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        return " ".join(
            seg.get("text", "")
            for seg in content
            if isinstance(seg, dict) and seg.get("type") == "text"
        ).strip()
    return str(content).strip()

def _write_score(score):
    out_dir = pathlib.Path("results")
    out_dir.mkdir(exist_ok=True, parents=True)
    with open(out_dir / f"smoke_{score['candidate']}.json", "w") as f:
        json.dump(score, f, indent=2)

def _add(score, pts, key, ok, msg=""):
    score["details"].append({"key": key, "points": (pts if ok else 0), "passed": bool(ok), "msg": msg})
    if ok:
        score["points"] += pts

# --- Smoke test (compile + basic invoke) ---
@pytest.mark.asyncio
async def test_smoke(monkeypatch):
    agent_path_env = os.getenv("CANDIDATE_AGENT_PATH", "").strip()
    agent_py_path = pathlib.Path(agent_path_env) if agent_path_env else DEFAULT_AGENT_PATH
    assert agent_py_path.exists(), f"agent.py not found at: {agent_py_path}"

    # Scoring model (10 pts total)
    score = {"candidate": CANDIDATE_NAME, "bucket": "smoke", "points": 0, "max_points": 7, "details": []}

    # A) Compile gate (2 pts)
    mod, err = _load_module(agent_py_path)
    if mod is None:
        _add(score, 2, "compile", False, err)
        _write_score(score)
        pytest.skip(err)

    try:
        app = _get_app(mod)
        has_invoke = hasattr(app, "invoke") or hasattr(app, "ainvoke")
        _add(score, 2, "compile", has_invoke, "compiled app must expose .invoke or .ainvoke")
        if not has_invoke:
            _write_score(score)
            pytest.skip("Compiled app has no .invoke or .ainvoke")
    except Exception as e:
        _add(score, 2, "compile", False, f"{type(e).__name__}: {e}")
        _write_score(score)
        pytest.skip(f"Compile failed: {e}")

    # B) Single invoke (8 pts, partial)
    try:
        initial_state = {"person": {"name": "Aliyan Ishfaq", "email": "aliyan@example.com", "company": "Example Inc", "role": "Software Engineer", "linkedin": "https://www.linkedin.com/in/aliyan-ishfaq"}}
        # Use async invoke if available, fallback to sync
        if hasattr(app, "ainvoke"):
            out = await app.ainvoke(initial_state)
        else:
            out = app.invoke(initial_state)
        _add(score, 2, "invoke_accepts_canonical_state", True, "")
    except Exception as e:
        _add(score, 2, "invoke_accepts_canonical_state", False, f"{type(e).__name__}: {e}")
        _write_score(score)
        pytest.fail("Smoke invoke failed")

    ok_dict = isinstance(out, dict)
    _add(score, 1, "output_is_dict", ok_dict, "output must be a dict")
    if not ok_dict:
        _write_score(score)
        pytest.fail("Output is not a dict")

    structured_info = out.get("extracted_info", None)
    with open("structured_info.json", "w") as f:
        f.write(str(structured_info))
    if structured_info is None or structured_info == {}:
        _add(score, 1, "structured_info_is_dict", False, "structured_info must be a dict")
        _write_score(score)
        pytest.fail("structured_info must be a dict")

    _add(score, 1, "structured_info_is_dict", True, "structured_info is non empty")
    
    # Check that structured_info has at least one key with a non-empty value
    # Convert Pydantic model to dict to check values
    if hasattr(structured_info, 'model_dump'):
        # Pydantic v2
        info_dict = structured_info.model_dump()
    elif hasattr(structured_info, 'dict'):
        # Pydantic v1
        info_dict = structured_info.dict()
    elif hasattr(structured_info, '__dict__'):
        # Fallback for objects with __dict__
        info_dict = vars(structured_info)
    elif isinstance(structured_info, dict):
        # Already a dictionary
        info_dict = structured_info
    else:
        try:
            info_dict = dict(structured_info) if hasattr(structured_info, '__iter__') else {'value': structured_info}
        except (TypeError, ValueError):
            info_dict = {'value': structured_info}
    
    has_content = any(
        value is not None and value != "" and value != [] and value != {}
        for value in info_dict.values()
    )
    _add(score, 1, "structured_info_has_content", has_content, 
         "structured_info must have at least one key with non-empty value")
    if not has_content:
        _write_score(score)
        pytest.fail("structured_info must have at least one key with non-empty value")
    
    _write_score(score)
