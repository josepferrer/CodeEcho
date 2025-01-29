from setuptools import setup, find_packages

setup(
    name="codeecho",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "python-dotenv>=0.19.0",
        "pydantic>=1.8.2",
    ],
    extras_require={
        "dev": [
            "pytest>=6.2.5",
            "pytest-cov>=2.12.1",
            "black>=21.7b0",
            "flake8>=3.9.2",
            "mypy>=0.910",
        ],
    },
    author="Josep Ferrer",
    description="A tool to understand repository data",
    keywords="code, repository, analysis",
    python_requires=">=3.7",
)