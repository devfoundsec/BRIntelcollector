from setuptools import setup

setup(
    name="brIntel",
    version="0.1.0",
    description="Ferramenta de coleta de inteligência em websites brasileiros.",
    author=["Matheus Oliveira matheusoliveiratux4me@gmail.com", "Julio Lira jul10l1r4@disroot.org"],
    author_email=["matheusoliveiratux4me@gmail.com", "jul10l1r4@disroot.org"],
    url="https://github.com/devfoundsec/BRIntelcollector",
    classifiers=[
        "Development Tools",
        "Science",
        "Library",
        "Security",
        "Threat Intelligent",
    ],
    install_requires=[
    "requests>=2.26.0",
    "beautifulsoup4>=4.10.0",
],
package_data={
        'brintelcollector': [
            'README.md',
        ],
    },
    license="MIT License",
    entry_points={
        'console_scripts': [
            'brintelcollector=brintelcollector.main:main'
        ]
    },
    packages=[
        "BRIntel",
    ]
)