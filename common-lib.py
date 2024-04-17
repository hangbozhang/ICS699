import sqlite3
from collections import Counter
import matplotlib.pyplot as plt


def get_top_names_by_change_type(repo_name, change_type, cursor):
    # Query to retrieve the most common names for a specific change type in a repository
    query = f'''
        SELECT ct.name, COUNT(ct.name) as name_count
        FROM filtered_change_table ct
        JOIN filtered_diff_table dt ON ct.diff_file = dt.diff_file
        WHERE dt.repo_name = ? AND ct.change_type = ?
        GROUP BY ct.name
        ORDER BY name_count DESC
        LIMIT 5
    '''
    cursor.execute(query, (repo_name, change_type))
    return cursor.fetchall()


def get_top_names_across_repos_by_change_type(change_type, cursor, min_repos=2, is_popular=False):
    # Query to retrieve the overall most common names for a specific change type across all repositories
    query = f'''
        SELECT ct.name, COUNT(ct.name) as name_count, COUNT(DISTINCT dt.repo_name) as repo_count
        FROM filtered_change_table ct
        JOIN filtered_diff_table dt ON ct.diff_file = dt.diff_file
        WHERE ct.change_type = ?
        GROUP BY ct.name
        HAVING repo_count >= ?
        ORDER BY name_count DESC
        LIMIT 5
    '''

    query2 = f'''
        SELECT ct.name, COUNT(ct.name) as name_count, COUNT(DISTINCT dt.repo_name) as repo_count
        FROM filtered_change_table ct
        JOIN filtered_diff_table dt ON ct.diff_file = dt.diff_file
        WHERE ct.change_type = ?
        GROUP BY ct.name
        HAVING repo_count >= ?
        ORDER BY repo_count DESC
        LIMIT 5
    '''

    if is_popular:
        cursor.execute(query2, (change_type, min_repos))
    else:
        cursor.execute(query, (change_type, min_repos))
    return cursor.fetchall()


def create_common_lib_table(cursor):
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS common_lib (
            repo_name TEXT PRIMARY KEY,
            added TEXT,
            removed TEXT,
            count_added TEXT,
            count_removed TEXT,
            top_lib TEXT
        )
    ''')


def insert_common_lib_data(repo_name, added_names, added_counts, removed_names, removed_counts, cursor):
    # Calculate overall top 5 names
    overall_top_names = set(added_names + removed_names)
    overall_top_counts = [added_counts[i] + removed_counts[i] for i in range(min(len(added_counts), len(removed_counts)))]

    # Ensure lists have exactly 5 elements
    overall_top_names = list(overall_top_names)[:5]
    # overall_top_counts = list(overall_top_counts)[:5]

    cursor.execute('''
        INSERT OR REPLACE INTO common_lib (repo_name, added, count_added, removed, count_removed, top_lib)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (repo_name, str(added_names), str(added_counts), str(removed_names), str(removed_counts), str(overall_top_names)))


def plot_occurrences(names_counts, change_type, switch=False):
    names, counts = zip(*names_counts)
    y_pos = range(len(names))
    plt.figure(figsize=(10, 6))

    plt.barh(y_pos, counts)

    if switch:
        plt.title(f'Total Occurrences for {change_type}')
    else:
        plt.title(f'Occurrences Across All Repos for {change_type}')

    plt.ylabel('Library Name')
    plt.xlabel('Occurrences')
    plt.yticks([])

    for i, (name, count) in enumerate(zip(names, counts)):
        plt.text(count + 1, i, f'{name}:{count}', va='center', ha='left')

    plt.tight_layout()
    plt.show()


def main():
    # Connect to the SQLite database
    conn = sqlite3.connect('SBOM')
    cursor = conn.cursor()

    create_common_lib_table(cursor)

    # Fetch repository names from diff_table
    cursor.execute('''SELECT DISTINCT repo_name FROM filtered_diff_table''')
    repo_names = [row[0] for row in cursor.fetchall()]

    added_names_counter = Counter()
    removed_names_counter = Counter()

    # Get the top 5 names for each change type in each repository
    for repo_name in repo_names:
        # print(f"Repository: {repo_name}")
        added_names = []
        removed_names = []
        for change_type in ['added', 'removed']:
            top_names_change_type = get_top_names_by_change_type(repo_name, change_type, cursor)
            # print(f"Top 5 Names for Change Type '{change_type}':")
            for name, count in top_names_change_type:
                # print(f"{name}: {count} occurrences")
                if change_type == 'added':
                    added_names.append(name)
                elif change_type == 'removed':
                    removed_names.append(name)

        # Increment the overall counter for each change type
        added_names_counter.update(set(added_names))
        removed_names_counter.update(set(removed_names))

        # Insert the data into the common_lib table
        insert_common_lib_data(repo_name, added_names, [added_names_counter[name] for name in added_names], removed_names, [removed_names_counter[name] for name in removed_names], cursor)

    # Get the overall top 5 names for each change type across all repositories
    for change_type in ['added', 'removed']:
        top_names_all_repos_change_type = get_top_names_across_repos_by_change_type(change_type, cursor)
        # plot_occurrences(top_names_all_repos_change_type, change_type, switch=True)
        print(f"Overall Top 5 Names for Change Type '{change_type}' Across All Repositories:")
        for name, name_count, repo_count in top_names_all_repos_change_type:
            print(f"{name}: {name_count} occurrences in {repo_count} repositories")
        print()

        print(f"Overall Most Popular 5 Names for Change Type '{change_type}'")
        top_names_all_repos_change_type = get_top_names_across_repos_by_change_type(change_type, cursor, is_popular=True)
        for name, name_count, repo_count in top_names_all_repos_change_type:
            print(f"{name}: {repo_count} repositories with {name_count} occurrences")
        print()
    # Get the overall top 5 names for each change type across all repositories
    # overall_top_added_names = added_names_counter.most_common(5)
    # overall_top_removed_names = removed_names_counter.most_common(5)

    # Plot the occurrences of the top names for each change type
    # plot_occurrences(overall_top_added_names, 'added')
    # plot_occurrences(overall_top_removed_names, 'removed')

    # print(f"Overall Top 5 Names for Change Type 'added' Across All Repositories:")
    # for name, count in overall_top_added_names:
    #     print(f"{name}: {count} occurrences")
    # print()

    # print(f"Overall Top 5 Names for Change Type 'removed' Across All Repositories:")
    # for name, count in overall_top_removed_names:
    #     print(f"{name}: {count} occurrences")
    # print()

    # Close the database connection
    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
