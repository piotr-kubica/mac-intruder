from setuptools import setup, find_packages

setup(
    name="mac-intruder",
    version="0.0.1",
    description="A Python script to detect new devices on a local network and send notifications via email.",
    author="Piotr Kubica",
    author_email="",
    url="https://github.com/piotr-kubica/mac-intruder",
    packages=find_packages(),
    install_requires=[
        "asttokens==3.0.0",
        "decorator==5.1.1",
        "executing==2.1.0",
        "freezegun==1.5.1",
        "iniconfig==2.0.0",
        "ipython==8.30.0",
        "jedi==0.19.2",
        "matplotlib-inline==0.1.7",
        "packaging==24.2",
        "parso==0.8.4",
        "pexpect==4.9.0",
        "pluggy==1.5.0",
        "prompt_toolkit==3.0.48",
        "ptyprocess==0.7.0",
        "pure_eval==0.2.3",
        "Pygments==2.18.0",
        "pytest==8.3.4",
        "python-dateutil==2.9.0.post0",
        "python-dotenv==1.0.1",
        "six==1.17.0",
        "stack-data==0.6.3",
        "traitlets==5.14.3",
        "typing_extensions==4.12.2",
        "wcwidth==0.2.13"
    ],
    entry_points={
        "console_scripts": [
            "mac-intruder=main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)