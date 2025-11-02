from pathlib import Path

from setuptools import find_packages, setup


README = Path(__file__).with_name("README.md").read_text(encoding="utf-8")


setup(
    name="brintelcollector",
    version="0.1.0",
    description="Threat intelligence collection toolkit",
    long_description=README,
    long_description_content_type="text/markdown",
    author="BRIntelcollector Maintainers",
    url="https://github.com/devfoundsec/BRIntelcollector",
    classifiers=[
        "Intended Audience :: Information Technology",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Topic :: Security",
    ],
    python_requires=">=3.10",
    install_requires=Path("requirements.txt").read_text().splitlines(),
    packages=find_packages(exclude=("tests", "tests.*")),
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "brintel=brintel.cli:app",
        ]
    },
    license="MIT",
)
