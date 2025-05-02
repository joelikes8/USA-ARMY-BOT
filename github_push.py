#!/usr/bin/env python3
import os
import requests
import base64
import json
import sys
from pathlib import Path
import time

# Variables
TOKEN = os.environ.get('GITHUB_TOKEN')
REPO_OWNER = 'joelikes8'
REPO_NAME = 'USA-ARMY-BOT'
BRANCH = 'main'

# Important file extensions to prioritize
PRIORITY_EXTENSIONS = ['.py', '.md', '.yml', '.yaml', '.toml', '.json']

# Rate limit handling
DELAY_BETWEEN_REQUESTS = 1  # seconds

def create_or_update_file(owner, repo, path, content, message, branch, token):
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

def get_file_list(exclude_patterns=None):
    if exclude_patterns is None:
        exclude_patterns = ['.git', '__pycache__', '.env', '.replit', '.breakpoints', '.config', '.upm', '.nix']
        
    file_list = []
    
    for path in Path('.').rglob('*'):
        if path.is_file():
            path_str = str(path)
            exclude = False
            for pattern in exclude_patterns:
                if pattern in path_str:
                    exclude = True
                    break
            
            if not exclude:
                file_list.append(path_str)
    
    # Sort files by priority (important code files first)
    priority_files = [f for f in file_list if any(f.endswith(ext) for ext in PRIORITY_EXTENSIONS)]
    other_files = [f for f in file_list if f not in priority_files]
    
    return priority_files + other_files

def push_files_to_github():
    files = get_file_list()
    print(f"Found {len(files)} files to push")
    
    # Make sure we have the token
    if not TOKEN:
        print('GitHub token is not set. Please set the GITHUB_TOKEN environment variable.')
        return False
    
    # Push the most important files first
    successful = 0
    for file_path in files:
        try:
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
            
            # Give status update every 5 files
            if successful % 5 == 0 and successful > 0:
                print(f"Progress: {successful}/{len(files)} files pushed successfully")
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    print(f'\n{successful} out of {len(files)} files pushed successfully!')
    return successful > 0

def check_repository_exists():
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

if __name__ == '__main__':
    print('Checking GitHub repository...')
    repo_exists = check_repository_exists()
    
    if not repo_exists:
        print(f"Creating repository {REPO_OWNER}/{REPO_NAME}...")
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
        else:
            print(f"Failed to create repository: {response.status_code} - {response.json().get('message', 'Unknown error')}")
            sys.exit(1)
    
    print('\nPushing files to GitHub repository...')
    success = push_files_to_github()
    
    if success:
        print(f'\nCode pushed to https://github.com/{REPO_OWNER}/{REPO_NAME}')
        print("You can view your repository at that URL.")
    else:
        print('\nFailed to push all code to GitHub')
        print("Some files may have been pushed successfully.")

