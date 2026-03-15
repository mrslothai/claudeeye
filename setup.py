from setuptools import setup, find_packages
import sys

# Platform-specific deps
install_requires = [
    "anthropic>=0.40.0",
    "PyQt6>=6.6.0",
    "Pillow>=10.0.0",
    "python-dotenv>=1.0.0",
    "pynput>=1.7.6",
    "requests>=2.28.0",
]

if sys.platform == "linux":
    install_requires.append("mss>=9.0.0")

setup(
    name="claudeeye",
    version="1.7.0",
    description="AI assistant that sees your screen — global hotkey, Claude integration",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Rajesh Chityal",
    author_email="rajesh@rajeshchityal.com",
    url="https://github.com/mrslothai/claudeeye",
    py_modules=["main", "gui", "tray", "screenshot", "claude_client", "hotkey"],
    install_requires=install_requires,
    entry_points={
        "console_scripts": [
            "claudeeye=main:main",
        ],
    },
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Utilities",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
    ],
)
