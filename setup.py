from setuptools import setup

setup(
    name="claudeeye",
    version="1.0.0",
    description="AI assistant that can see your screen",
    py_modules=["main", "gui", "tray", "screenshot", "claude_client"],
    install_requires=[
        "anthropic>=0.40.0",
        "PyQt6>=6.6.0",
        "Pillow>=10.0.0",
        "python-dotenv>=1.0.0",
        "mss>=9.0.0",
    ],
    entry_points={
        "console_scripts": [
            "claudeeye=main:main",
        ],
    },
    python_requires=">=3.9",
)
