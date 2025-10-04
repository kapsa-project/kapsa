from setuptools import setup, find_packages

setup(
    name="kapsa-operator",
    version="0.1.0",
    description="Kubernetes-native deployment platform operator",
    author="Kapsa Project",
    author_email="",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.12",
    install_requires=[
        "kopf>=1.37.2",
        "kubernetes>=29.0.0",
        "aiohttp>=3.9.5",
        "GitPython>=3.1.43",
        "structlog>=24.1.0",
        "prometheus-client>=0.20.0",
        "pydantic>=2.7.1",
        "pydantic-settings>=2.2.1",
    ],
    extras_require={
        "dev": [
            "black>=24.4.2",
            "ruff>=0.4.3",
            "mypy>=1.10.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "kapsa-operator=kapsa.main:main",
        ],
    },
)
