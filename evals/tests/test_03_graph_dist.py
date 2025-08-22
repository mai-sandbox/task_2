import os
import json
import pathlib
import pytest
import sys

from tests.utils.graph_comparison import compute_graph_distances

CANDIDATE_NAME = os.getenv("CANDIDATE_NAME", "claude-code-mcp").strip()

def _write_score(score):
    out = pathlib.Path("results")
    out.mkdir(parents=True, exist_ok=True)
    with open(out / f"graph_dist_{score['candidate']}.json", "w") as f:
        json.dump(score, f, indent=2)

def _add(score, pts, key, ok, msg=""):
    score["details"].append({"key": key, "points": (pts if ok else 0), "passed": bool(ok), "msg": msg})
    if ok: 
        score["points"] += pts

def test_graph_distance():
    score = {"candidate": CANDIDATE_NAME, "bucket": "graph_dist", "points": 0, "max_points": 5, "details": []}
    
    try:
        # Import candidate agent
        candidate_src_path = str(pathlib.Path("../src").resolve())
        sys.path.insert(0, candidate_src_path)
        
        # Clear any cached agent modules to ensure fresh import
        import importlib
        modules_to_remove = [mod for mod in sys.modules.keys() if mod.startswith('agent')]
        for mod in modules_to_remove:
            del sys.modules[mod]
            
        from agent.graph import graph as candidate_graph
        
        # Remove candidate path and add expert path
        sys.path.remove(candidate_src_path)
        expert_src_path = str(pathlib.Path("expert_src").resolve())
        sys.path.insert(0, expert_src_path)
        
        # Clear cached agent modules again for expert import
        modules_to_remove = [mod for mod in sys.modules.keys() if mod.startswith('agent')]
        for mod in modules_to_remove:
            del sys.modules[mod]
            
        from agent.graph import graph as gold_graph

        # draw gold graph
        with open("gold_graph.png", "wb") as f:
            f.write(gold_graph.get_graph().draw_mermaid_png())
        
        # Generate graph visualization
        with open("candidate_graph.png", "wb") as f:
            f.write(candidate_graph.get_graph().draw_mermaid_png())
        
        # Calculate edit distance
        distance = compute_graph_distances(candidate_graph, gold_graph)["edit_distance"]
        print(f"Structural edit distance: {distance}")
        
        # Calculate score based on the formula
        MAX_PTS = 5
        D_CAP = 10
        
        points = max(0, round(MAX_PTS * (1 - min(distance, D_CAP) / D_CAP)))
        print(f"Score: {points}/{MAX_PTS} points")
        
        _add(score, points, "graph_distance", True, f"Edit distance: {distance}")
        
    except Exception as e:
        _add(score, 0, "graph_distance", False, f"Error: {type(e).__name__}: {e}")
        pytest.fail(f"Graph distance test failed: {e}")
    
    _write_score(score)