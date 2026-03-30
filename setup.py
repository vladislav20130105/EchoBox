from setuptools import setup, find_packages

setup(
    name="echobox",
    version="1.7.1",
    description="EchoBox - Простая библиотека звуков",
    long_description="Простая и удобная библиотека звуков с поддержкой MP3 и WAV файлов",
    author="EchoBox Team",
    author_email="support@echobox.com",
    url="https://github.com/vladislav20130105/EchoBox",
    packages=find_packages(),
    py_modules=["echobox"],
    install_requires=[
        "pygame>=2.5.2",
        "pyaudio>=0.2.11",
        "numpy>=1.24.3",
        "pydub>=0.25.1",
        "sounddevice>=0.4.6",
        "simpleaudio>=1.0.4",
        "mutagen>=1.46.0",
        "Pillow>=9.0.0",
    ],
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "echobox=echobox:main",
        ],
    },
)
