#!/usr/bin/env python3
"""
Validation script for langgraph.json configuration file.
Checks structure, dependencies, and graph references against LangGraph platform requirements.
"""

import json
import os
import sys
import importlib.util
from pathlib import Path

def validate_json_structure(config_path: str) -> tuple[bool, dict]:
    """Validate the basic JSON structure and required fields."""
    
    print("=" * 60)
    print("Validating langgraph.json Structure")
    print("=" * 60)
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print("✅ JSON file is valid and parseable")
        
        # Check required top-level fields
        required_fields = ["dependencies", "graphs"]
        optional_fields = ["env"]
        
        for field in required_fields:
            if field not in config:
                print(f"❌ Missing required field: {field}")
                return False, {}
            print(f"✅ Required field present: {field}")
        
        for field in optional_fields:
            if field in config:
                print(f"✅ Optional field present: {field}")
        
        # Validate dependencies structure
        if not isinstance(config["dependencies"], list):
            print("❌ 'dependencies' must be a list")
            return False, {}
        
        if len(config["dependencies"]) == 0:
            print("❌ 'dependencies' list cannot be empty")
            return False, {}
        
        print(f"✅ Dependencies list contains {len(config['dependencies'])} packages")
        
        # Validate graphs structure
        if not isinstance(config["graphs"], dict):
            print("❌ 'graphs' must be an object/dictionary")
            return False, {}
        
        if len(config["graphs"]) == 0:
            print("❌ 'graphs' object cannot be empty")
            return False, {}
        
        print(f"✅ Graphs object contains {len(config['graphs'])} graph(s)")
        
        # Validate env field if present
        if "env" in config:
            if not isinstance(config["env"], str):
                print("❌ 'env' must be a string path to environment file")
                return False, {}
            print(f"✅ Environment file specified: {config['env']}")
        
        return True, config
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON format: {e}")
        return False, {}
    except FileNotFoundError:
        print(f"❌ Configuration file not found: {config_path}")
        return False, {}
    except Exception as e:
        print(f"❌ Error reading configuration: {e}")
        return False, {}


def validate_dependencies(dependencies: list) -> bool:
    """Validate that all specified dependencies are available."""
    
    print("\n" + "=" * 60)
    print("Validating Dependencies")
    print("=" * 60)
    
    all_valid = True
    
    for dep in dependencies:
        try:
            # Try to import the package
            if dep == "langchain-anthropic":
                import langchain_anthropic
                print(f"✅ {dep}: Available")
            elif dep == "langchain-core":
                import langchain_core
                print(f"✅ {dep}: Available")
            elif dep == "langgraph":
                import langgraph
                print(f"✅ {dep}: Available")
            elif dep == "tavily-python":
                import tavily
                print(f"✅ {dep}: Available")
            elif dep == "pydantic":
                import pydantic
                print(f"✅ {dep}: Available")
            else:
                # Generic import attempt
                spec = importlib.util.find_spec(dep.replace("-", "_"))
                if spec is not None:
                    print(f"✅ {dep}: Available")
                else:
                    print(f"❌ {dep}: Not found")
                    all_valid = False
                    
        except ImportError:
            print(f"❌ {dep}: Import failed")
            all_valid = False
        except Exception as e:
            print(f"❌ {dep}: Error checking - {e}")
            all_valid = False
    
    return all_valid


def validate_graphs(graphs: dict) -> bool:
    """Validate that all specified graph references are valid."""
    
    print("\n" + "=" * 60)
    print("Validating Graph References")
    print("=" * 60)
    
    all_valid = True
    
    for graph_name, graph_path in graphs.items():
        print(f"\nValidating graph '{graph_name}': {graph_path}")
        
        # Parse the graph path (format: "./path/to/file.py:variable_name")
        if ":" not in graph_path:
            print(f"❌ Invalid graph path format. Expected 'file.py:variable', got: {graph_path}")
            all_valid = False
            continue
        
        file_path, variable_name = graph_path.split(":", 1)
        
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"❌ Graph file not found: {file_path}")
            all_valid = False
            continue
        
        print(f"✅ Graph file exists: {file_path}")
        
        # Try to import and check the variable
        try:
            # Convert file path to module path
            module_path = file_path.replace("./", "").replace("/", ".").replace(".py", "")
            
            # Import the module
            spec = importlib.util.spec_from_file_location(module_path, file_path)
            if spec is None or spec.loader is None:
                print(f"❌ Cannot create module spec for: {file_path}")
                all_valid = False
                continue
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_path] = module
            spec.loader.exec_module(module)
            
            # Check if the variable exists
            if not hasattr(module, variable_name):
                print(f"❌ Variable '{variable_name}' not found in {file_path}")
                all_valid = False
                continue
            
            print(f"✅ Variable '{variable_name}' found in module")
            
            # Get the variable and check if it's a compiled graph
            graph_var = getattr(module, variable_name)
            
            # Check if it has the expected methods of a compiled graph
            expected_methods = ["invoke", "ainvoke", "stream", "astream"]
            missing_methods = []
            
            for method in expected_methods:
                if not hasattr(graph_var, method):
                    missing_methods.append(method)
            
            if missing_methods:
                print(f"❌ Graph missing expected methods: {missing_methods}")
                all_valid = False
            else:
                print(f"✅ Graph has all expected methods: {expected_methods}")
            
            # Try to get the graph's schema/structure info
            try:
                if hasattr(graph_var, 'get_graph'):
                    graph_info = graph_var.get_graph()
                    print(f"✅ Graph structure accessible")
                    
                    # Count nodes and edges
                    if hasattr(graph_info, 'nodes') and hasattr(graph_info, 'edges'):
                        node_count = len(graph_info.nodes)
                        edge_count = len(graph_info.edges)
                        print(f"✅ Graph has {node_count} nodes and {edge_count} edges")
                    
                elif hasattr(graph_var, 'graph'):
                    print(f"✅ Graph object has graph attribute")
                else:
                    print(f"⚠️  Cannot access graph structure (may still be valid)")
                    
            except Exception as e:
                print(f"⚠️  Cannot inspect graph structure: {e}")
            
        except Exception as e:
            print(f"❌ Error importing graph: {e}")
            all_valid = False
    
    return all_valid


def validate_environment_file(env_path: str) -> bool:
    """Validate the environment file if specified."""
    
    print("\n" + "=" * 60)
    print("Validating Environment File")
    print("=" * 60)
    
    if not env_path:
        print("ℹ️  No environment file specified")
        return True
    
    if not os.path.exists(env_path):
        print(f"❌ Environment file not found: {env_path}")
        return False
    
    print(f"✅ Environment file exists: {env_path}")
    
    try:
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        env_vars = []
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    var_name = line.split('=')[0]
                    env_vars.append(var_name)
                else:
                    print(f"⚠️  Line {line_num}: Invalid format (missing '='): {line}")
        
        print(f"✅ Environment file contains {len(env_vars)} variables")
        
        # Check for common LangGraph environment variables
        common_vars = ["ANTHROPIC_API_KEY", "TAVILY_API_KEY", "OPENAI_API_KEY"]
        found_vars = [var for var in common_vars if var in env_vars]
        
        if found_vars:
            print(f"✅ Found common API key variables: {found_vars}")
        else:
            print("ℹ️  No common API key variables found (may be set elsewhere)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading environment file: {e}")
        return False


def main():
    """Main validation function."""
    
    print("LangGraph Configuration Validation")
    print("=" * 60)
    
    config_path = "langgraph.json"
    
    # Step 1: Validate JSON structure
    structure_valid, config = validate_json_structure(config_path)
    if not structure_valid:
        print("\n❌ Configuration structure validation failed!")
        return False
    
    # Step 2: Validate dependencies
    deps_valid = validate_dependencies(config["dependencies"])
    
    # Step 3: Validate graph references
    graphs_valid = validate_graphs(config["graphs"])
    
    # Step 4: Validate environment file (if specified)
    env_valid = validate_environment_file(config.get("env"))
    
    # Final results
    print("\n" + "=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)
    
    all_valid = structure_valid and deps_valid and graphs_valid and env_valid
    
    if all_valid:
        print("🎉 ALL VALIDATIONS PASSED!")
        print("✅ JSON structure is valid")
        print("✅ All dependencies are available")
        print("✅ All graph references are valid")
        print("✅ Environment configuration is valid")
        print("✅ Configuration is ready for LangGraph platform deployment")
    else:
        print("❌ SOME VALIDATIONS FAILED!")
        if not structure_valid:
            print("❌ JSON structure validation failed")
        if not deps_valid:
            print("❌ Dependencies validation failed")
        if not graphs_valid:
            print("❌ Graph references validation failed")
        if not env_valid:
            print("❌ Environment file validation failed")
    
    print("=" * 60)
    return all_valid


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
