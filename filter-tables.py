import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('SBOM')
cursor = conn.cursor()

cursor.execute('''
        CREATE TABLE IF NOT EXISTS filtered_change_table (
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

# Create Diff Table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS filtered_diff_table (
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

# Dictionary to store ecosystems used in each repository
repo_ecosystems = {}

# SQL query to find distinct repositories
repos_query = "SELECT DISTINCT repo_name FROM filtered_diff_table"
cursor.execute(repos_query)
repos = cursor.fetchall()

filter_query = "SELECT * FROM change_table WHERE manifest NOT LIKE '%.lock' AND manifest NOT LIKE '%lock.json'"
cursor.execute(filter_query)
filtered = cursor.fetchall()

filtered_diff_query = "SELECT dt.diff_file, dt.base_sha, dt.base_tag, dt.base_data, dt.head_sha, dt.head_tag, dt.head_data, dt.repo_name FROM diff_table dt JOIN filtered_change_table ct ON dt.diff_file = ct.diff_file GROUP BY dt.diff_file"
cursor.execute(filtered_diff_query)
filtered_diff = cursor.fetchall()

for row in filtered:
    cursor.execute('''
        INSERT OR REPLACE INTO filtered_change_table (change_id, change_type, manifest, ecosystem, name, version, package_url, license, source_repository_url, scope, vulnerabilities, diff_file)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', row)

for row in filtered_diff:
    cursor.execute('''
        INSERT OR REPLACE INTO filtered_diff_table (diff_file, base_sha, base_tag, base_data, head_sha, head_tag, head_data, repo_name)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', row)

# Iterate over each repository and find ecosystems
for repo in repos:
    repo_name = repo[0]

    # SQL query to find distinct ecosystems for the current repository
    ecosystems_query = f"""
        SELECT DISTINCT filtered_change_table.ecosystem
        FROM filtered_change_table
        JOIN filtered_diff_table ON filtered_change_table.diff_file = filtered_diff_table.diff_file
        WHERE filtered_diff_table.repo_name = '{repo_name}'
    """
    cursor.execute(ecosystems_query)
    ecosystems = cursor.fetchall()

    # Update the dictionary with ecosystems used in the current repository
    repo_ecosystems[repo_name] = [ecosystem[0] for ecosystem in ecosystems]

# Close the database connection
conn.commit()
conn.close()

# Print ecosystems used in each repository and count of repositories for each ecosystem
for repo_name, ecosystems in repo_ecosystems.items():
    print(f"\nRepository: '{repo_name}'")
    print("Ecosystems:")
    for ecosystem in ecosystems:
        print(f"- {ecosystem}")

# Count how many repositories have used each ecosystem
ecosystem_count = {}
for ecosystems in repo_ecosystems.values():
    for ecosystem in ecosystems:
        ecosystem_count[ecosystem] = ecosystem_count.get(ecosystem, 0) + 1

print("\nNumber of Repositories for Each Ecosystem:")
for ecosystem, count in ecosystem_count.items():
    print(f"{ecosystem}: {count} repositories")
