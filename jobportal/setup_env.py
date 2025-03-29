"""
Environment Variables Setup Guide

This script helps you set up the required environment variables for the Job Portal application.
Follow the instructions below to configure your environment.

Required Environment Variables:
- SECRET_KEY: Django secret key
- DEBUG: Set to 'True' for development, 'False' for production
- ALLOWED_HOSTS: Comma-separated list of allowed hosts
- DATABASE_URL: Database connection URL (for production)
- EMAIL_HOST: SMTP server host
- EMAIL_PORT: SMTP server port
- EMAIL_HOST_USER: SMTP username
- EMAIL_HOST_PASSWORD: SMTP password
- DEFAULT_FROM_EMAIL: Default sender email
- OPENAI_API_KEY: Your OpenAI API key for the chatbot functionality

How to set up:
1. Create a .env file in the root directory of the project
2. Add the environment variables in the format KEY=VALUE
3. Make sure to keep the .env file secure and never commit it to version control

Example .env file:
SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=your_email@gmail.com
OPENAI_API_KEY=your_openai_api_key
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Check if required environment variables are set
required_vars = [
    'SECRET_KEY',
    'DEBUG',
    'ALLOWED_HOSTS',
    'OPENAI_API_KEY'
]

missing_vars = []
for var in required_vars:
    if not os.getenv(var):
        missing_vars.append(var)

if missing_vars:
    print("Warning: The following required environment variables are not set:")
    for var in missing_vars:
        print(f"- {var}")
    print("\nPlease set these variables in your .env file or environment.")
else:
    print("All required environment variables are set!")

# Print instructions for getting OpenAI API key if it's missing
if 'OPENAI_API_KEY' in missing_vars:
    print("\nTo get an OpenAI API key:")
    print("1. Go to https://platform.openai.com/api-keys")
    print("2. Sign up or log in to your OpenAI account")
    print("3. Create a new API key")
    print("4. Add the key to your .env file as OPENAI_API_KEY=your_key_here")

