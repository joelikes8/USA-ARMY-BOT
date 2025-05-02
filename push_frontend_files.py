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

# Frontend files to push
FRONTEND_FILES = [
    # Template files
    'templates/announcements.html',
    'templates/base.html',
    'templates/index.html',
    'templates/verifications.html',
    
    # CSS files
    'static/css/styles.css',
    
    # Icons/Images
    'generated-icon.png',
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

def push_frontend_files():
    """Push frontend files to GitHub"""
    if not TOKEN:
        print('GitHub token is not set. Please set the GITHUB_TOKEN environment variable.')
        return False
    
    print(f"Preparing to push {len(FRONTEND_FILES)} frontend files")
    
    # Push each frontend file
    successful = 0
    for file_path in FRONTEND_FILES:
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
                try:
                    # If it's an image, read it as binary and encode to base64
                    with open(file_path, 'rb') as f:
                        content_bytes = f.read()
                        content = base64.b64encode(content_bytes).decode('utf-8')
                    
                    # For binary files, we need to use the base64 content directly
                    print(f'Pushing binary file: {file_path}...')
                    url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_path}'
                    headers = {
                        'Authorization': f'Bearer {TOKEN}',
                        'Accept': 'application/vnd.github.v3+json'
                    }
                    
                    # Check if file exists to get its SHA
                    response = requests.get(url, headers=headers, params={'ref': BRANCH})
                    existing_sha = response.json().get('sha') if response.status_code == 200 else None
                    
                    # Prepare the request data
                    data = {
                        'message': f'Add/Update binary file {file_path}',
                        'content': content,
                        'branch': BRANCH
                    }
                    
                    if existing_sha:
                        data['sha'] = existing_sha
                    
                    # Make the request to create/update the file
                    response = requests.put(url, headers=headers, data=json.dumps(data))
                    if response.status_code in (200, 201):
                        successful += 1
                        print(f"✓ Successfully pushed binary file {file_path}")
                    else:
                        error_msg = response.json().get('message', 'Unknown error')
                        print(f'✗ Error creating/updating binary file {file_path}: {response.status_code} - {error_msg}')
                    
                    # Skip to next file
                    time.sleep(DELAY_BETWEEN_REQUESTS)
                    continue
                except Exception as e:
                    print(f'Error processing binary file {file_path}: {e}')
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
    
    print(f'\n{successful} out of {len(FRONTEND_FILES)} frontend files pushed successfully!')
    return successful > 0

if __name__ == '__main__':
    print('Pushing frontend files to GitHub repository...')
    success = push_frontend_files()
    
    if success:
        print(f'\nFrontend files pushed to https://github.com/{REPO_OWNER}/{REPO_NAME}')
        print("The web dashboard UI files are now uploaded!")
    else:
        print('\nFailed to push frontend files to GitHub')