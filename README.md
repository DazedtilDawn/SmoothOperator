# Smooth Operator

A Python-based task orchestration and validation system that helps ensure code quality, documentation standards, and development best practices are followed throughout the development lifecycle.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/SmoothOperator.git
cd SmoothOperator
```

2. **Quick Start**: Simply double-click `run_migration.bat` and the system will:
   - Create a virtual environment if needed
   - Install required dependencies
   - Set up necessary directories
   - Present a checklist selection menu

Alternatively, for manual setup:

3. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Simple Execution
1. Double-click `run_migration.bat`
2. Select a checklist from the menu
3. Follow the prompts

### Programmatic Usage
The Smooth Operator system provides a flexible framework for defining and executing task checklists with validation:

```python
from orchestrator import Orchestrator

# Initialize the orchestrator
orchestrator = Orchestrator()

# Load a checklist
orchestrator.load_checklist(".checklists/example.yml")

# Start a phase
orchestrator.start_phase("Setup")

# Execute tasks with validation
result = orchestrator.execute_task("Setup", "Git Configuration")
if result.success:
    print("Git configuration validated successfully!")
```

### Project Structure
```
SmoothOperator/
├── .checklists/           # YAML checklist definitions
│   └── example.yml       # Sample checklist
├── run_migration.bat     # Double-click entry point
├── orchestrator.py       # Main orchestration logic
├── requirements.txt      # Project dependencies
├── validation_system/    # Validation components
│   ├── core.py          # Core validation logic
│   ├── validate_git.py  # Git validation
│   └── validate_docs.py # Documentation validation
└── docs/                # Documentation
    ├── api/            # API documentation
    ├── tutorials/      # Usage tutorials
    └── examples/       # Example code
```

### Key Features

1. **Zero Configuration Setup**
   - Double-click execution
   - Auto-creates virtual environment
   - Self-healing directory structure
   - Guided checklist creation

2. **Task Orchestration**
   - YAML-based checklist definitions
   - Phase-based execution flow
   - Clear visual progress tracking
   - Comprehensive validation system

3. **Validation System**
   - Git configuration validation
   - Documentation standards checking
   - Code quality assessment
   - Artifact management

4. **Visual Feedback**
   - Progress indicators
   - Success/failure markers
   - Detailed validation reports
   - Clear error messages

## Contributing

We welcome contributions! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`python -m pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

Please ensure your code follows our coding standards and includes appropriate tests and documentation.

## License

This project is licensed under the MIT License - see below for details:

```
MIT License

Copyright (c) 2024 Smooth Operator

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
``` 