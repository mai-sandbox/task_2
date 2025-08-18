#!/usr/bin/env python3
"""Check dependency compatibility and version requirements."""

import subprocess
import sys
from packaging import version
from packaging.specifiers import SpecifierSet

def get_installed_version(package_name):
    """Get the installed version of a package."""
    try:
        result = subprocess.run(
            ["pip", "show", package_name],
            capture_output=True,
            text=True,
            check=True
        )
        for line in result.stdout.split('\n'):
            if line.startswith('Version:'):
                return line.split(':')[1].strip()
    except subprocess.CalledProcessError:
        return None

def check_requirement(requirement_str):
    """Parse and check a requirement string."""
    # Parse requirement string (e.g., "langgraph>=0.2.52")
    if '>=' in requirement_str:
        package_name, min_version = requirement_str.split('>=')
        return package_name.strip(), f">={min_version.strip()}"
    elif '==' in requirement_str:
        package_name, exact_version = requirement_str.split('==')
        return package_name.strip(), f"=={exact_version.strip()}"
    else:
        return requirement_str.strip(), ""

def main():
    """Check all dependencies for compatibility."""
    print("=" * 60)
    print("DEPENDENCY COMPATIBILITY CHECK")
    print("=" * 60)
    
    # Requirements from pyproject.toml
    requirements = [
        "langgraph>=0.2.52",
        "langsmith>=0.1.147",
        "langchain-community>=0.3.8",
        "tavily-python>=0.5.0",
        "langchain_anthropic>=0.3.0",
    ]
    
    # Additional important dependencies to check
    additional_deps = [
        "langchain-core",
        "langchain",
        "pydantic",
        "anthropic",
    ]
    
    print("\nChecking required dependencies from pyproject.toml:")
    print("-" * 40)
    
    all_compatible = True
    issues = []
    
    for req in requirements:
        package_name, spec = check_requirement(req)
        installed = get_installed_version(package_name.replace('_', '-'))
        
        if installed:
            if spec:
                specifier = SpecifierSet(spec)
                if version.parse(installed) in specifier:
                    print(f"  ✓ {package_name}: {installed} (required {spec})")
                else:
                    print(f"  ✗ {package_name}: {installed} (required {spec}) - VERSION MISMATCH")
                    issues.append(f"{package_name}: installed {installed}, required {spec}")
                    all_compatible = False
            else:
                print(f"  ✓ {package_name}: {installed}")
        else:
            print(f"  ✗ {package_name}: NOT INSTALLED")
            issues.append(f"{package_name}: not installed")
            all_compatible = False
    
    print("\nChecking additional important dependencies:")
    print("-" * 40)
    
    for dep in additional_deps:
        installed = get_installed_version(dep)
        if installed:
            print(f"  ✓ {dep}: {installed}")
        else:
            print(f"  ⚠ {dep}: NOT INSTALLED (may be optional)")
    
    # Check for known compatibility issues
    print("\nChecking for known compatibility issues:")
    print("-" * 40)
    
    # Check LangGraph and LangChain compatibility
    langgraph_ver = get_installed_version("langgraph")
    langchain_core_ver = get_installed_version("langchain-core")
    
    if langgraph_ver and langchain_core_ver:
        lg_major = version.parse(langgraph_ver).major
        lc_major = version.parse(langchain_core_ver).major
        
        if lg_major == 0 and lc_major == 0:
            print(f"  ✓ LangGraph {langgraph_ver} and LangChain-Core {langchain_core_ver} are compatible")
        else:
            print(f"  ⚠ Check compatibility between LangGraph {langgraph_ver} and LangChain-Core {langchain_core_ver}")
    
    # Check Pydantic version (should be 2.x for latest LangChain)
    pydantic_ver = get_installed_version("pydantic")
    if pydantic_ver:
        pyd_major = version.parse(pydantic_ver).major
        if pyd_major == 2:
            print(f"  ✓ Pydantic {pydantic_ver} is compatible (v2.x)")
        else:
            print(f"  ✗ Pydantic {pydantic_ver} may have compatibility issues (expected v2.x)")
            issues.append(f"Pydantic version {pydantic_ver} may not be compatible")
            all_compatible = False
    
    print("\n" + "=" * 60)
    
    if all_compatible:
        print("✅ ALL DEPENDENCIES ARE COMPATIBLE")
        print("\nAll required packages are installed with compatible versions.")
    else:
        print("⚠️ SOME COMPATIBILITY ISSUES DETECTED")
        print("\nIssues found:")
        for issue in issues:
            print(f"  - {issue}")
        print("\nConsider running: pip install --upgrade -e .")
    
    print("=" * 60)
    
    return 0 if all_compatible else 1

if __name__ == "__main__":
    sys.exit(main())
