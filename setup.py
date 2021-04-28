from setuptools import setup, find_packages

setup(
    name="pdclient",
    version="0.3.0",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
        ],
    },
    install_requires=[
        'requests',
    ],
    extras_require={
        'testing': [
            'pytest',
        ],
    },
)