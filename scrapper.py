import os
import requests
import re

# Search for Solidity repositories using the GitHub API
response = requests.get('https://api.github.com/search/repositories?q=language:solidity')
repositories = response.json()['items']

for repository in repositories:
    # Check if the repository has an open source license
    license_response = requests.get(repository['url'] + '/license')
    if license_response.json()['license']['spdx_id'] not in ['MIT', 'Apache-2.0', 'GPL-2.0', 'GPL-3.0']:
        continue
    
    # Initialize the list to store the Solidity files
    solidity_files = []

    # Fetch the repository contents
    contents_url = repository['url'] + '/contents/'
    contents_response = requests.get(contents_url)

    # Iterate over the contents of the repository
    for content in contents_response.json():
        # Check if the content is a file with the .sol extension
        if content['type'] == 'file' and content['name'].endswith('.sol'):
            file_response = requests.get(content['download_url'])
            solidity_files.append({
                'name': content['name'],
                'content': file_response.text
            })
            
            # Check if the Solidity file has associated unit tests
            test_file_name = content['name'].replace('.sol', 'Test.sol')
            for test_content in contents_response.json():
                if test_content['type'] == 'file' and test_content['name'] == test_file_name:
                    # Fetch the content of the unit test file
                    test_file_response = requests.get(test_content['download_url'])
                    solidity_files.append({
                        'name': test_content['name'],
                        'content': test_file_response.text
                    })
                    break
    
    # Store the extracted files in a SQLite database
    import sqlite3

    conn = sqlite3.connect('solidity_files.db')
    c = conn.cursor()

    # Create a table to store the Solidity files
    c.execute('''
        CREATE TABLE IF NOT EXISTS solidity_files (
            repository_id INTEGER,
            name TEXT,
            content TEXT,
            PRIMARY KEY (repository_id, name)
        )
    ''')

    # Insert the Solidity files into the database
    for file in solidity_files:
        c.execute('''
            INSERT OR REPLACE INTO solidity_files (repository_id, name, content)
            VALUES (?, ?, ?)
        ''', (repository['id'], file['name'], file['content']))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()
