from unittest.mock import MagicMock, mock_open, patch

import pytest

from dependency_detective.dependency_detective import (
    analyze_file, analyze_project, find_python_files,
    generate_new_requirements, get_installed_packages, get_latest_version,
    is_standard_library, main, read_requirements)


def test_find_python_files(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    (d / "test1.py").touch()
    (d / "test2.py").touch()
    (d / "not_python.txt").touch()

    files = find_python_files(str(tmp_path), [])
    assert len(files) == 2
    assert all(file.endswith('.py') for file in files)


def test_analyze_file():
    file_content = """
import os
import sys as system
from datetime import datetime

def main():
    print(os.getcwd())
    print(system.version)
    """

    with patch('builtins.open', mock_open(read_data=file_content)):
        imports = analyze_file('dummy_file.py')

    assert imports == {'os', 'sys', 'datetime'}


@patch('dependency_detective.dependency_detective.distributions')
def test_get_installed_packages(mock_distributions):
    mock_dist1 = MagicMock()
    mock_dist1.metadata = {'Name': 'package1'}
    mock_dist1.version = '1.0.0'
    mock_dist2 = MagicMock()
    mock_dist2.metadata = {'Name': 'package2'}
    mock_dist2.version = '2.0.0'
    mock_distributions.return_value = [mock_dist1, mock_dist2]

    packages = get_installed_packages()
    assert packages == {'package1': '1.0.0', 'package2': '2.0.0'}


def test_read_requirements():
    req_content = """
package1==1.0.0
package2>=2.0.0
package3
"""
    with patch('builtins.open', mock_open(read_data=req_content)):
        reqs = read_requirements('requirements.txt')

    assert reqs == {'package1': '1.0.0', 'package2': '>=2.0.0', 'package3': None}


@patch('dependency_detective.dependency_detective.requests.get')
def test_get_latest_version(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {"info": {"version": "2.0.0"}}
    mock_get.return_value = mock_response
    version = get_latest_version('pytest')
    assert version == "2.0.0"

    mock_get.side_effect = Exception("Network error")
    version = get_latest_version('pytest')
    assert version is None


@patch('dependency_detective.dependency_detective.get_latest_version')
def test_generate_new_requirements(mock_get_latest_version, tmp_path):
    analysis = {
        'used_packages': {'pytest', 'flake8'},
        'installed_packages': {'pytest': '4.0.0', 'flake8': '3.9.0'}
    }
    output_file = tmp_path / "new_requirements.txt"
    generate_new_requirements(analysis, str(output_file))
    assert output_file.exists()
    content = output_file.read_text()

    expected_content = "flake8==3.9.0\npytest==4.0.0\n"
    assert content == expected_content

    lines = content.strip().split('\n')
    assert len(lines) == 2
    assert set(lines) == {'flake8==3.9.0', 'pytest==4.0.0'}


@patch('dependency_detective.dependency_detective.find_python_files')
@patch('dependency_detective.dependency_detective.analyze_file')
@patch('dependency_detective.dependency_detective.get_installed_packages')
@patch('dependency_detective.dependency_detective.read_requirements')
@patch('dependency_detective.dependency_detective.is_standard_library')
def test_analyze_project(mock_is_standard_library, mock_read_req, mock_get_installed, mock_analyze_file, mock_find_files):
    mock_find_files.return_value = ['file1.py', 'file2.py']
    mock_analyze_file.side_effect = [
        {'os', 'sys', 'requests'},
        {'datetime', 'flask'}
    ]
    mock_get_installed.return_value = {
        'os': '1.0', 'sys': '2.0', 'datetime': '3.0',
        'requests': '2.26.0', 'flask': '2.0.1', 'unused_pkg': '4.0'
    }
    mock_read_req.return_value = {'requests': '2.26.0', 'flask': '2.0.1', 'outdated_pkg': '3.0'}
    mock_is_standard_library.side_effect = lambda x: x in {'os', 'sys', 'datetime'}

    analysis = analyze_project('/dummy/path', 'requirements.txt', [])

    assert analysis['used_packages'] == {'requests', 'flask'}
    assert analysis['unused_or_nested_packages'] == {'unused_pkg'}
    assert analysis['missing_packages'] == set()
    assert analysis['outdated_packages'] == {'outdated_pkg'}
    assert analysis['installed_packages'] == mock_get_installed.return_value
    assert analysis['requirements'] == mock_read_req.return_value

    # Verify that is_standard_library was called at least once for each installed package
    for package in mock_get_installed.return_value:
        mock_is_standard_library.assert_any_call(package)

    # Verify that is_standard_library was called for each analyzed import
    for imports in mock_analyze_file.side_effect:
        for imp in imports:
            mock_is_standard_library.assert_any_call(imp)


@patch('dependency_detective.dependency_detective.analyze_project')
@patch('dependency_detective.dependency_detective.generate_report')
@patch('dependency_detective.dependency_detective.generate_new_requirements')
@patch('argparse.ArgumentParser.parse_args')
def test_main(mock_parse_args, mock_generate_new_requirements, mock_generate_report, mock_analyze_project):
    mock_parse_args.return_value = type('Args', (), {
        'project_directory': '/test/project',
        'requirements': 'requirements.txt',
        'output': None,
        'new_requirements': 'new_requirements.txt',
        'verbose': False,
        'exclude': ['venv', '.venv', 'env', '.env']
    })
    mock_analyze_project.return_value = {'test': 'analysis'}

    main()

    mock_analyze_project.assert_called_once_with('/test/project', 'requirements.txt', ['venv', '.venv', 'env', '.env'])
    mock_generate_report.assert_called_once_with({'test': 'analysis'}, None)
    mock_generate_new_requirements.assert_called_once_with(
        {'test': 'analysis'}, 'new_requirements.txt')


def test_is_standard_library():
    # flake8: noqa
    assert is_standard_library('os') == True
    assert is_standard_library('sys') == True
    assert is_standard_library('datetime') == True
    assert is_standard_library('pytest') == False
    assert is_standard_library('flask') == False


if __name__ == '__main__':
    pytest.main()
