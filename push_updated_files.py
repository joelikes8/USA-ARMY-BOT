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

# New files to push
UPDATED_FILES = [
    'render.yaml',
    'requirements_for_render.txt',
    'generate_requirements.py',
    'webapp.py',
    'wsgi.py',
    'Procfile',
    'render_build.sh'
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

def push_updated_files():
    """Push updated files to GitHub"""
    if not TOKEN:
        print('GitHub token is not set. Please set the GITHUB_TOKEN environment variable.')
        return False
    
    print(f"Preparing to push {len(UPDATED_FILES)} updated files")
    
    # Push each updated file
    successful = 0
    for file_path in UPDATED_FILES:
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
                f'Update {file_path} for Render deployment', 
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
    
    print(f'\n{successful} out of {len(UPDATED_FILES)} files pushed successfully!')
    return successful > 0

if __name__ == '__main__':
    print('Pushing updated files to GitHub repository...')
    success = push_updated_files()
    
    if success:
        print(f'\nUpdated files pushed to https://github.com/{REPO_OWNER}/{REPO_NAME}')
        print("Your Render deployment configuration is now updated!")
    else:
        print('\nFailed to push updated files to GitHub')
