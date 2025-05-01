#!/usr/bin/env python3
import os
import sys

def generate_requirements_from_pyproject():
    """Generate requirements.txt from pyproject.toml dependencies"""
    dependencies = [
        "discord-py>=2.5.2",
        "email-validator>=2.2.0",
        "flask>=3.1.0",
        "flask-sqlalchemy>=3.1.1",
        "gunicorn>=23.0.0",
        "psycopg2-binary>=2.9.10",
        "python-dotenv>=1.1.0",
        "requests>=2.32.3",
        "roblox>=2.0.0",
    ]
    
    # Get all dependencies from pyproject.toml
    with open('requirements_for_render.txt', 'w') as f:
        f.write('\n'.join(dependencies))
    
    print("Generated requirements_for_render.txt")

if __name__ == "__main__":
    generate_requirements_from_pyproject()
