from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="stem-grad-assistant",
    version="1.0.0",
    author="STEM Grad Assistant Team",
    author_email="team@stemgradassistant.com",
    description="AI-powered STEM graduate admissions assistant",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/stem-grad-assistant/stem-grad-assistant",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Framework :: FastAPI",
        "Topic :: Education",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "black>=23.11.0",
            "isort>=5.12.0",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
            "httpx>=0.25.2",
        ],
    },
    entry_points={
        "console_scripts": [
            "stem-grad-assistant=app.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "app": ["static/*", "data/*"],
    },
)