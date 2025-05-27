from setuptools import setup, find_packages

setup(
    name="agents",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "openai==1.12.0",
        "python-dotenv>=0.19.0",
    ],
) 