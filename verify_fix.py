#!/usr/bin/env python3
"""Verify the dictionary access pattern fix."""

import re

# Read the graph.py file
with open('src/agent/graph.py', 'r') as f:
    content = f.read()

# Check for dictionary-style access to state.person
dict_pattern = re.compile(r"state\.person\[")
dict_matches = dict_pattern.findall(content)

# Check for correct dot notation access
dot_pattern = re.compile(r"state\.person\.(email|name|linkedin|role|company)")
dot_matches = dot_pattern.findall(content)

print("Verification of state.person access patterns:")
print("-" * 50)

if dict_matches:
    print(f"❌ Found {len(dict_matches)} dictionary-style accesses (need fixing)")
    for match in dict_matches:
        print(f"   - {match}")
else:
    print("✅ No dictionary-style access found (state.person['key'])")

if dot_matches:
    print(f"✅ Found {len(dot_matches)} correct dot notation accesses")
    print(f"   Fields accessed: {', '.join(set(dot_matches))}")
else:
    print("⚠️  No dot notation access found")

# Verify the specific lines that were fixed
lines_to_check = [86, 87, 88, 89, 90, 91, 92, 93, 94]
lines = content.split('\n')

print("\nFixed lines verification (85-94):")
print("-" * 50)
for line_num in lines_to_check:
    if line_num <= len(lines):
        line = lines[line_num - 1]  # Convert to 0-based index
        if 'state.person' in line:
            if '[' in line and ']' in line and 'state.person[' in line:
                print(f"❌ Line {line_num}: Still using dictionary access")
            else:
                print(f"✅ Line {line_num}: Using dot notation correctly")

print("\n" + "=" * 50)
if not dict_matches and dot_matches:
    print("✅ SUCCESS: All state.person accesses use correct dot notation!")
else:
    print("❌ ISSUE: Dictionary-style access still present or no accesses found")
