from setuptools import setup, find_packages

setup(
    name="costpilot",
    version="1.0.0",
    description="AWS Cloud Cost Optimization Engine",
    author="Hunter Spence",
    packages=find_packages(),
    install_requires=["boto3>=1.28.0", "click>=8.0", "jinja2>=3.0"],
    entry_points={"console_scripts": ["costpilot=costpilot.cli:main"]},
    python_requires=">=3.10",
)
