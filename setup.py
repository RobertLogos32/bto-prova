# File: /data/chats/o1xbzd/workspace/uploads/bot_otp/setup.py

from setuptools import setup, find_packages

setup(
    name="otp_bot",
    version="0.1",
    packages=find_packages(),    install_requires=[
        "psycopg2-binary",
        "pyTelegramBotAPI",
    ],
    author="Developer",
    author_email="dev@example.com",
    description="Telegram Bot for OTP system with database integration",
)
