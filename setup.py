from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="dependency-detective",
    version="0.1.0",
    author="Hamed Haghjo",
    author_email="hamedhaghjo@hotmail.com",
    description="A tool to analyze Python project dependencies",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/RealWorga/DependencyDetective",
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "dependency-detective=dependency_detective.dependency_detective:main",
        ],
    },
    install_requires=[
        "setuptools",
        "requests",
    ],
    extras_require={
        "dev": [
            "pytest",
            "flake8",
            "twine",
        ],
    },
)
