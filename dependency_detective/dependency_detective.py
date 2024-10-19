#!/usr/bin/env python3
"""
DependencyDetective: A tool to analyze Python project dependencies.

This script scans Python projects to identify installed packages,
compare them with requirements.txt (if exists), and analyze usage across files.
It generates a comprehensive report on package usage and potential issues.
"""

import argparse
import ast
import importlib
import logging
import os
import sys
from importlib.metadata import distributions
from typing import Dict, List, Set

import requests


def setup_logging(verbose: bool) -> None:
    """Configure logging based on verbosity."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format='%(levelname)s: %(message)s')


def is_standard_library(module_name: str) -> bool:
    """Check if a module is part of the Python standard library."""
    try:
        module_spec = importlib.util.find_spec(module_name)
        if module_spec is None:
            return False
        return 'site-packages' not in module_spec.origin
    except ImportError:
        return False


def find_python_files(directory: str, exclude_dirs: List[str]) -> List[str]:
    """Find all Python files in the given directory and its subdirectories."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files


class ImportVisitor(ast.NodeVisitor):
    def __init__(self):
        self.imports = set()

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name.split('.')[0])

    def visit_ImportFrom(self, node):
        if node.level == 0:  # absolute import
            self.imports.add(node.module.split('.')[0])


def analyze_file(file_path: str) -> Set[str]:
    """Analyze a Python file for imports."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            tree = ast.parse(file.read(), filename=file_path)

        visitor = ImportVisitor()
        visitor.visit(tree)

        return visitor.imports
    except Exception as e:
        logging.error(f"Error analyzing file {file_path}: {e}")
        return set()


def get_installed_packages() -> Dict[str, str]:
    """Get a dict of all installed packages and their versions."""
    return {dist.metadata['Name']: dist.version for dist in distributions()}


def read_requirements(file_path: str) -> Dict[str, str]:
    """Read requirements.txt and return a dict of package names and versions."""
    requirements = {}
    if not os.path.exists(file_path):
        logging.warning(f"Requirements file not found: {file_path}")
        return requirements

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                parts = line.split('==')
                if len(parts) == 2:
                    requirements[parts[0]] = parts[1]
                elif '>=' in line:
                    name, version = line.split('>=')
                    requirements[name.strip()] = f'>={version.strip()}'
                else:
                    requirements[line] = None
    return requirements


def get_latest_version(package_name: str) -> str:
    """Get the latest version of a package from PyPI."""
    try:
        url = f"https://pypi.org/pypi/{package_name}/json"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data["info"]["version"]
    except Exception as e:
        logging.warning(f"Failed to fetch latest version for {package_name}: {e}")
        return None


def analyze_project(project_dir: str, requirements_file: str, exclude_dirs: List[str]) -> Dict:
    """Analyze the project directory and generate a comprehensive report."""
    python_files = find_python_files(project_dir, exclude_dirs)
    installed_packages = get_installed_packages()
    requirements = read_requirements(requirements_file)

    project_imports = set()
    for file_path in python_files:
        project_imports.update(analyze_file(file_path))

    # Filter out standard library modules
    project_imports = {imp for imp in project_imports if not is_standard_library(imp)}

    used_packages = project_imports.intersection(installed_packages.keys())
    unused_packages = {pkg for pkg in installed_packages.keys() if not is_standard_library(pkg)} - used_packages
    missing_packages = project_imports - set(installed_packages.keys())
    outdated_packages = set(requirements.keys()) - used_packages

    return {
        'used_packages': used_packages,
        'unused_or_nested_packages': unused_packages,
        'missing_packages': missing_packages,
        'outdated_packages': outdated_packages,
        'installed_packages': installed_packages,
        'requirements': requirements
    }


def generate_report(analysis: Dict, output_file: str = None) -> None:
    """Generate and print the analysis report."""
    report = "Dependency Detective Report\n"
    report += "===========================\n\n"

    sections = [
        ("Used Packages", analysis['used_packages']),
        ("Unused or Nested Packages", analysis['unused_or_nested_packages']),
        ("Missing Packages", analysis['missing_packages']),
        ("Potentially Outdated Packages", analysis['outdated_packages'])
    ]

    for title, packages in sections:
        report += f"{title}:\n"
        report += "-" * (len(title) + 1) + "\n"
        for package in sorted(packages):
            version = analysis['installed_packages'].get(package, "Not installed")
            req_version = analysis['requirements'].get(package, "Not specified")
            report += f"- {package} (Installed: {version}, Required: {req_version})\n"
        report += "\n"

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        logging.info(f"Report saved to {output_file}")
    else:
        print(report)


def generate_new_requirements(analysis: Dict, output_file: str) -> None:
    """Generate a new requirements.txt with only necessary packages."""
    necessary_packages = analysis['used_packages']
    with open(output_file, 'w', encoding='utf-8') as f:
        for package in sorted(necessary_packages):
            version = analysis['installed_packages'].get(package)
            if version:
                f.write(f"{package}=={version}\n")
            else:
                f.write(f"{package}\n")
    logging.info(f"New requirements file generated: {output_file}")


def main():
    """Main function to run the DependencyDetective."""
    parser = argparse.ArgumentParser(description="Analyze Python project dependencies.")
    parser.add_argument("project_directory", help="Path to the Python project directory")
    parser.add_argument("--requirements", "-r", default="requirements.txt",
                        help="Path to the requirements.txt file (default: %(default)s)")
    parser.add_argument("--output", "-o", help="Output file for the analysis report")
    parser.add_argument("--new-requirements", "-n",
                        help="Generate a new requirements.txt with only necessary packages")
    parser.add_argument("--exclude", "-e", nargs='+', default=['venv', '.venv', 'env', '.env'],
                        help="Directories to exclude from analysis (default: venv .venv env .env)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    setup_logging(args.verbose)

    try:
        analysis = analyze_project(args.project_directory, args.requirements, args.exclude)
        generate_report(analysis, args.output)

        if args.new_requirements:
            generate_new_requirements(analysis, args.new_requirements)

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
