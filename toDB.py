import os
import json
import csv
import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('SBOM')
cursor = conn.cursor()

# Create Repo Table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS repo_table (
        repo_name TEXT PRIMARY KEY,
        repo_owner TEXT,
        repo_url TEXT,
        commits INTEGER,
        releases INTEGER
    )
''')

# Create Diff Table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS diff_table (
        diff_file TEXT PRIMARY KEY,
        base_sha TEXT,
        base_tag TEXT,
        base_data TEXT,
        head_sha TEXT,
        head_tag TEXT,
        head_data TEXT,
        repo_name TEXT,
        FOREIGN KEY (repo_name) REFERENCES repo_table (repo_name)
    )
''')

# Create Change Table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS change_table (
        change_id INTEGER PRIMARY KEY,
        change_type TEXT,
        manifest TEXT,
        ecosystem TEXT,
        name TEXT,
        version TEXT,
        package_url TEXT,
        license TEXT,
        source_repository_url TEXT,
        scope TEXT,
        vulnerabilities TEXT,
        diff_file TEXT,
        FOREIGN KEY (diff_file) REFERENCES diff_table (diff_file)
    )
''')

# Specify the path to the main directory
script_directory = os.path.dirname(os.path.realpath(__file__))
base_dir = 'sbom-releases'
destination_path = os.path.join(script_directory, base_dir)
repo_csv = os.path.join(script_directory, 'sbom-releases/results2.csv')

with open(repo_csv, 'r') as csv_file:
    repo_csv_reader = csv.DictReader(csv_file)

    for row_number, repo_row in enumerate(repo_csv_reader):
        try:
            repo_owner, repo_name = repo_row['name'].split('/')
            commits = int(repo_row['commits'])
            releases = int(repo_row['releases'])
            repo_url = f"github.com/{repo_owner}/{repo_name}"

            cursor.execute('''
                INSERT OR REPLACE INTO repo_table (repo_name, repo_owner, repo_url, commits, releases)
                VALUES (?, ?, ?, ?, ?  )
            ''', (repo_name, repo_owner, repo_url, commits, releases))

            repo_sha = f"{repo_name}_sha.csv"
            repo_path = os.path.join(destination_path, repo_name)
            sha_path = os.path.join(repo_path, repo_sha)

            # Read and parse the JSON file
            with open(sha_path, 'r') as sha_csv_file:
                sha_csv_file_reader = csv.DictReader(sha_csv_file)

                for diff_row in sha_csv_file_reader:
                    diff_file = diff_row['Filename']
                    base_sha = diff_row['Base']
                    base_tag = diff_row['Base Tag']
                    base_date = diff_row['Base Date']
                    head_sha = diff_row['Head']
                    head_tag = diff_row['Head Tag']
                    head_date = diff_row['Head Date']

                    # Insert data into Diff Table
                    cursor.execute('''
                        INSERT OR REPLACE INTO diff_table (diff_file, base_sha, base_tag, base_data, head_sha, head_tag, head_data, repo_name)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        diff_file,
                        base_sha,
                        base_tag,
                        base_date,
                        head_sha,
                        head_tag,
                        head_date,
                        repo_name
                    ))

            if os.path.isdir(repo_path):
                for file_name in os.listdir(repo_path):
                    if file_name.endswith('.json'):
                        file_path = os.path.join(repo_path, file_name)

                        with open(file_path, 'r') as json_file:
                            try:
                                json_data = json.load(json_file)
                            except json.decoder.JSONDecodeError as e:
                                print(f"Error: Unable to parse JSON file {file_name}: {e}")
                                continue

                        # Insert data into Change Table
                        for change in json_data:
                            cursor.execute('''
                                INSERT OR REPLACE INTO change_table (change_type, manifest, ecosystem, name, version, package_url, license, source_repository_url, scope, vulnerabilities, diff_file)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                change.get('change_type', ''),
                                change.get('manifest', ''),
                                change.get('ecosystem', ''),
                                change.get('name', ''),
                                change.get('version', ''),
                                change.get('package_url', ''),
                                change.get('license', ''),
                                change.get('source_repository_url', ''),
                                change.get('scope', ''),
                                json.dumps(change.get('vulnerabilities', [])),
                                file_name
                            ))
        except KeyError as e:
            print(f"KeyError in row {row_number + 1}: {str(e)}")
            print(f"Row data: {repo_row}")
# Commit changes and close the connection
conn.commit()
conn.close()
