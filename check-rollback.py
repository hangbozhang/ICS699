import sqlite3
from semantic_version import Version


def is_valid_version(version_string):
    try:
        Version(version_string)
        return True
    except ValueError:
        return False


def get_dependencies_in_repo(repo_name, dep_name, cursor):
    """Get the dependencies for a repository."""
    query = f'''
        SELECT dt.repo_name, ct.name, ct.manifest, ct.change_type, ct.version, dt.head_tag, dt.head_data
        FROM change_table as ct
        JOIN diff_table as dt ON ct.diff_file = dt.diff_file
        WHERE dt.repo_name = ? AND ct.name = ?
        ORDER BY dt.head_data DESC
    '''

    cursor.execute(query, (repo_name, dep_name))
    dep_data = cursor.fetchall()

    # Check for rollbacks within the same head_tag
    versions_by_head_tag_manifest = {}
    rollback_info = []

    for entry in dep_data:
        head_tag = entry[5]  # Assuming head_tag is at index 5
        manifest = entry[2]  # Assuming manifest is at index 2
        change_type = entry[3]  # Assuming change_type is at index 3
        version = entry[4]  # Assuming version is at index 4

        key = (head_tag, manifest)
        if key not in versions_by_head_tag_manifest:
            versions_by_head_tag_manifest[key] = {'added': [], 'removed': []}

        versions_in_head_tag_manifest = versions_by_head_tag_manifest[key]

        if change_type == 'added' and is_valid_version(version):
            versions_in_head_tag_manifest['added'].append(Version(version))
        elif change_type == 'removed' and is_valid_version(version):
            versions_in_head_tag_manifest['removed'].append(Version(version))

        # Check for rollbacks within each head_tag and manifest
        added_versions = sorted(versions_in_head_tag_manifest['added'], reverse=True)
        removed_versions = sorted(versions_in_head_tag_manifest['removed'], reverse=True)

        for removed_version in removed_versions:
            for added_version in added_versions:
                if removed_version > added_version:
                    rollback_info.append((dep_name, head_tag, manifest, removed_version, added_version))

    return dep_data, rollback_info


def get_all_dependencies_for_the_repo(repo_name, cursor):
    """Get all the dependencies for a repository."""
    query = f'''
        SELECT DISTINCT ct.name
        FROM change_table as ct
        JOIN diff_table as dt ON ct.diff_file = dt.diff_file
        WHERE dt.repo_name = ?
    '''

    cursor.execute(query, (repo_name,))
    return cursor.fetchall()


def get_highest_added_versions_for_repo(repo_name, cursor):
    """Get the highest added version for each dependency in the repository."""
    query = '''
        SELECT ct.name, ct.version
        FROM change_table as ct
        JOIN diff_table as dt ON ct.diff_file = dt.diff_file
        WHERE dt.repo_name = ? AND ct.change_type = 'added'
    '''

    cursor.execute(query, (repo_name,))
    results = cursor.fetchall()

    highest_added_versions = {}
    for name, version in results:
        if name not in highest_added_versions or version > highest_added_versions[name]:
            highest_added_versions[name] = version

    return [(name, str(version)) for name, version in highest_added_versions.items()]


def insert_highest_added_versions_into_table(repo_name, highest_added_versions, cursor):
    """Insert highest added versions into the version_table."""
    create_table_query = '''
        CREATE TABLE IF NOT EXISTS version_table (
            repo_name TEXT,
            dependency_name TEXT,
            highest_version TEXT,
            PRIMARY KEY (repo_name, dependency_name)
        )
    '''
    cursor.execute(create_table_query)

    insert_query = '''
        INSERT INTO version_table (repo_name, dependency_name, highest_version)
        VALUES (?, ?, ?)
    '''

    for dep_name, highest_version in highest_added_versions:
        cursor.execute(insert_query, (repo_name, dep_name, highest_version))


def main():
    # Connect to the SQLite database
    conn = sqlite3.connect('SBOM')
    cursor = conn.cursor()

    # Fetch repository names from diff_table
    cursor.execute('''SELECT DISTINCT repo_name FROM diff_table''')
    repo_names = [row[0] for row in cursor.fetchall()]

    for repo_name in repo_names:
        # Get all the dependencies for the repository
        dependencies = get_all_dependencies_for_the_repo(repo_name, cursor)
        dependency_names = [dep[0] for dep in dependencies]

        print(f"Highest added versions for {repo_name}:")
        highest_added_versions = get_highest_added_versions_for_repo(repo_name, cursor)
        for dep_name, highest_version in highest_added_versions:
            print(f"{dep_name}: {highest_version}")

        # Insert highest added versions into the version_table
        insert_highest_added_versions_into_table(repo_name, highest_added_versions, cursor)

        print(f"Rollback check in Repository: {repo_name}")
        for dep_name in dependency_names:
            # Get the dependencies for the repository and check for updates and rollbacks
            dep_data, rollback_info = get_dependencies_in_repo(repo_name, dep_name, cursor)

            if rollback_info:
                for rollback_dep_name, head_tag, manifest, removed_version, added_version in rollback_info:
                    print(
                        f"  Rollback Dependency: {rollback_dep_name}, Head Tag: {head_tag}, Manifest: {manifest}, "
                        f"Rolled back from version {removed_version} to {added_version}")
                print()

        print()

    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()
