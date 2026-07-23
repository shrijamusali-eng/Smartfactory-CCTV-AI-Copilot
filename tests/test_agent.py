import sys
import os

# Force Python to find the root folder modules ('database', 'agents', 'rag')
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Now imports will work cleanly!
from agents.copilot import ask

print("--- Agent Test 1: Stats Query ---")
print(ask("How many total violations are there?"))

print("\n--- Agent Test 2: Analytical Query ---")
print(ask("Which zone has the most violations?"))