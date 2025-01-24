# Getting Started with Smooth Operator

This tutorial will guide you through setting up and using the Smooth Operator system for managing operational workflows.

## Prerequisites

- Python 3.8 or higher
- Git
- Virtual environment tool (venv)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/SmoothOperator.git
cd SmoothOperator
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Creating Your First Checklist

1. Create a new file `my_checklist.yaml` in the `.checklists` directory:
```yaml
name: My First Checklist
description: A simple checklist for testing the system
phases:
  - name: Setup
    description: Initial setup phase
    tasks:
      - name: Git Configuration
        description: Verify Git setup
        validation:
          script: validate_git.py
      - name: Documentation
        description: Check documentation standards
        validation:
          script: validate_docs.py
```

2. Create a Python script to run the checklist:
```python
from orchestrator import Orchestrator

# Initialize the orchestrator
orchestrator = Orchestrator()

# Load your checklist
orchestrator.load_checklist(".checklists/my_checklist.yaml")

# Start the Setup phase
orchestrator.start_phase("Setup")

# Execute tasks
result = orchestrator.execute_task("Setup", "Git Configuration")
if result.success:
    print("Git configuration is valid!")
    print("Generated artifacts:", result.artifacts)
else:
    print("Error:", result.error_message)

result = orchestrator.execute_task("Setup", "Documentation")
if result.success:
    print("Documentation meets standards!")
else:
    print("Documentation needs improvement:", result.error_message)
```

## Understanding Validation Results

Each validation script produces:
1. A success/failure status
2. Validation messages
3. Metrics about the validation
4. Artifact files with detailed information

Example validation result:
```json
{
    "success": true,
    "messages": [],
    "metrics": {
        "git_configured": true,
        "gitignore_score": 1.0
    }
}
```

## Next Steps

1. Explore the [API Documentation](../api/README.md)
2. Check out more [Examples](../examples/)
3. Learn about [Custom Validation Scripts](./custom_validations.md) 