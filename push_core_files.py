#!/usr/bin/env python3
import os
import requests
import base64
import json
import sys
import time

# GitHub API token and repository information
TOKEN = os.environ.get('GITHUB_TOKEN')
REPO_OWNER = 'joelikes8'
REPO_NAME = 'USA-ARMY-BOT'
BRANCH = 'main'

# Core project files to push
CORE_FILES = [
    # Main application files
    'main.py',
    'bot.py',
    'database.py',
    'models.py',
    'webapp.py',
    
    # Configuration files
    'pyproject.toml',
    'render.yaml',
    'Procfile',
    'runtime.txt',
    'README.md',
    '.gitignore',
    
    # Utility files
    'utils/embed_helpers.py',
    
    # Bot command modules
    'cogs/announce_commands.py',
    'cogs/ticket_commands.py',
    'cogs/verify_commands.py',
]

# Rate limit handling
DELAY_BETWEEN_REQUESTS = 0.5  # seconds

def create_or_update_file(owner, repo, path, content, message, branch, token):
    """Create or update a file in the GitHub repository using the GitHub API"""
    url = f'https://api.github.com/repos/{owner}/{repo}/contents/{path}'
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Check if file exists to get its SHA
    try:
        response = requests.get(url, headers=headers, params={'ref': branch})
        existing_sha = response.json().get('sha') if response.status_code == 200 else None
    except Exception as e:
        print(f"Error checking file existence: {e}")
        existing_sha = None
    
    # Prepare the request data
    data = {
        'message': message,
        'content': base64.b64encode(content.encode()).decode('utf-8'),
        'branch': branch
    }
    
    if existing_sha:
        data['sha'] = existing_sha
    
    # Make the request to create/update the file
    try:
        response = requests.put(url, headers=headers, data=json.dumps(data))
        if response.status_code in (200, 201):
            return True
        else:
            error_msg = response.json().get('message', 'Unknown error')
            print(f'Error creating/updating file {path}: {response.status_code} - {error_msg}')
            return False
    except Exception as e:
        print(f"Error uploading file: {e}")
        return False

def push_core_files():
    """Push only core project files to GitHub"""
    if not TOKEN:
        print('GitHub token is not set. Please set the GITHUB_TOKEN environment variable.')
        return False
    
    print(f"Preparing to push {len(CORE_FILES)} core files")
    
    # Push each core file
    successful = 0
    for file_path in CORE_FILES:
        try:
            # Check if file exists locally
            if not os.path.exists(file_path):
                print(f"Skipping {file_path} - file not found locally")
                continue
            
            # Try to read the file as text
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                print(f'Skipping binary file: {file_path}')
                continue
            
            print(f'Pushing {file_path}...')
            result = create_or_update_file(
                REPO_OWNER, 
                REPO_NAME, 
                file_path, 
                content, 
                f'Add/Update {file_path}', 
                BRANCH, 
                TOKEN
            )
            
            if result:
                successful += 1
                print(f"✓ Successfully pushed {file_path}")
            else:
                print(f"✗ Failed to push {file_path}")
            
            # Respect rate limits
            time.sleep(DELAY_BETWEEN_REQUESTS)
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    print(f'\n{successful} out of {len(CORE_FILES)} core files pushed successfully!')
    return successful > 0

def check_repository_exists():
    """Check if the GitHub repository exists"""
    url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}'
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        print(f"Repository {REPO_OWNER}/{REPO_NAME} exists.")
        return True
    elif response.status_code == 404:
        print(f"Repository {REPO_OWNER}/{REPO_NAME} doesn't exist yet.")
        return False
    else:
        print(f"Error checking repository: {response.status_code} - {response.json().get('message', 'Unknown error')}")
        return False

def create_repository():
    """Create a new GitHub repository"""
    url = 'https://api.github.com/user/repos'
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    data = {
        'name': REPO_NAME,
        'description': 'USA Army Discord Bot - Python-based Discord bot with Roblox verification capabilities',
        'private': False
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 201:
        print("Repository created successfully!")
        return True
    else:
        print(f"Failed to create repository: {response.status_code} - {response.json().get('message', 'Unknown error')}")
        return False

if __name__ == '__main__':
    print('Checking GitHub repository...')
    repo_exists = check_repository_exists()
    
    if not repo_exists:
        print(f"Creating repository {REPO_OWNER}/{REPO_NAME}...")
        if not create_repository():
            sys.exit(1)  # Exit if repository creation fails
    
    print('\nPushing core files to GitHub repository...')
    success = push_core_files()
    
    if success:
        print(f'\nCore project files pushed to https://github.com/{REPO_OWNER}/{REPO_NAME}')
        print("You can view your repository at that URL.")
    else:
        print('\nFailed to push core project files to GitHub')
