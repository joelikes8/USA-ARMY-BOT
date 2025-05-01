#!/usr/bin/env python3
import os
import requests
import base64
import subprocess
import json
import sys
from pathlib import Path

# Variables
TOKEN = os.environ.get('GITHUB_TOKEN')
REPO_OWNER = 'joelikes8'
REPO_NAME = 'USA-ARMY-BOT'
BRANCH = 'main'

def get_sha_for_branch(owner, repo, branch, token):
    url = f'https://api.github.com/repos/{owner}/{repo}/branches/{branch}'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['commit']['sha']
    elif response.status_code == 404:
        # Branch doesn't exist, will be created with the first commit
        return None
    else:
        print(f'Error getting branch SHA: {response.status_code}')
        print(response.json())
        sys.exit(1)

def create_or_update_file(owner, repo, path, content, message, branch, token, sha=None):
    url = f'https://api.github.com/repos/{owner}/{repo}/contents/{path}'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Check if file exists to get its SHA
    existing_sha = None
    if sha is None:
        response = requests.get(url, headers=headers, params={'ref': branch})
        if response.status_code == 200:
            existing_sha = response.json()['sha']
    
    data = {
        'message': message,
        'content': base64.b64encode(content.encode()).decode('utf-8'),
        'branch': branch
    }
    
    if existing_sha or sha:
        data['sha'] = existing_sha or sha
    
    response = requests.put(url, headers=headers, data=json.dumps(data))
    if response.status_code in (200, 201):
        return response.json()
    else:
        print(f'Error creating/updating file {path}: {response.status_code}')
        print(response.json())
        return None

def get_file_list(exclude_patterns=None):
    if exclude_patterns is None:
        exclude_patterns = ['.git', '__pycache__', '.env', '.replit', '.breakpoints', '.config']
        
    file_list = []
    
    for path in Path('.').rglob('*'):
        if path.is_file():
            exclude = False
            for pattern in exclude_patterns:
                if pattern in str(path):
                    exclude = True
                    break
            
            if not exclude:
                file_list.append(str(path))
    
    return file_list

def push_files_to_github():
    files = get_file_list()
    
    # Make sure we have the token
    if not TOKEN:
        print('GitHub token is not set. Please set the GITHUB_TOKEN environment variable.')
        return False
    
    # Push each file
    for file_path in files:
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
        
        if not result:
            print(f'Failed to push {file_path}')
    
    print('\nAll files pushed successfully!')
    return True

if __name__ == '__main__':
    print('Pushing files to GitHub repository...')
    success = push_files_to_github()
    if success:
        print(f'\nCode pushed to https://github.com/{REPO_OWNER}/{REPO_NAME}')
    else:
        print('\nFailed to push code to GitHub')
