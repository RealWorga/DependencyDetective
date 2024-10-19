# DependencyDetective

[![PyPI version](https://badge.fury.io/py/dependency-detective.svg)](https://badge.fury.io/py/dependency-detective)
[![Python Versions](https://img.shields.io/pypi/pyversions/dependency-detective.svg)](https://pypi.org/project/dependency-detective/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://github.com/RealWorga/DependencyDetective/workflows/Python%20package/badge.svg)](https://github.com/RealWorga/DependencyDetective/actions)

DependencyDetective is a powerful tool for analyzing Python project dependencies. It scans your project to identify installed packages, compare them with requirements.txt (if it exists), and analyze usage across files. This tool helps maintain clean and efficient Python projects by providing insights into package usage and potential issues.

## Features

- Scans all Python files in a project to find imported packages
- Identifies used packages and unused or nested packages
- Detects missing packages not listed in requirements.txt
- Highlights potentially outdated packages in requirements.txt
- Excludes standard library modules from analysis
- Allows exclusion of specific directories from analysis
- Generates comprehensive reports for easy dependency management
- Creates a new requirements.txt with only necessary packages

## Installation

```bash
pip install dependency-detective
```

## Usage

```bash
dependency-detective /path/to/your/project [options]
```

Optional arguments:
- `--requirements`, `-r`: Specify a custom path to the requirements.txt file (default: requirements.txt)
- `--output`, `-o`: Specify an output file for the analysis report
- `--new-requirements`, `-n`: Generate a new requirements.txt with only necessary packages
- `--exclude`, `-e`: Specify directories to exclude from analysis (default: venv .venv env .env)
- `--verbose`, `-v`: Enable verbose logging

## Example

```bash
dependency-detective /path/to/your/project -r custom_requirements.txt -o analysis_report.txt -n new_requirements.txt -e venv example_dir
```

This command will:
1. Analyze the project at `/path/to/your/project`
2. Use `custom_requirements.txt` as the requirements file
3. Save the analysis report to `analysis_report.txt`
4. Generate a new requirements file named `new_requirements.txt` with only necessary packages
5. Exclude the `venv` and `example_dir` directories from the analysis

## Output

DependencyDetective generates a report that includes:

- Used Packages: Packages that are imported and used in your project
- Unused or Nested Packages: Packages that are installed but not directly imported in your project (they might be dependencies of other packages)
- Missing Packages: Packages that are imported in your project but not installed
- Potentially Outdated Packages: Packages listed in requirements.txt but not used in the project

The new requirements file (if requested) will contain only the packages directly used in your project, helping to minimize unnecessary dependencies.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.