from setuptools import setup, find_packages

setup(
    name="appbot-client",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"":"src"},
    install_requires=[
        "requests>=2.28.0",
        "python-dotenv>=1.0.0",
    ],
    python_requires=">=3.7",
)
