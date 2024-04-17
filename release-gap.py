import sqlite3
import re
import statistics

# Connect to the SQLite database
conn = sqlite3.connect('SBOM')
cursor = conn.cursor()

# Create release gap Table
cursor.execute('''
	CREATE TABLE IF NOT EXISTS gap_table (
		repo_name TEXT PRIMARY KEY,
		number_of_changes INTEGER,
		release_gap TEXT,
		average INTEGER,
		median INTEGER
		)
''')

cursor.execute('''SELECT repo_name FROM repo_table''')

rows = cursor.fetchall()

repos = [row[0] for row in rows]
diff_files = []
count = 0

for repo in repos:
	cursor.execute('''SELECT diff_file FROM filtered_diff_table WHERE repo_name = ?''', (repo,))
	rows = cursor.fetchall()
	changes = []
	changes_gap = []
	if len(rows) == 0:
		print(f"{repo} has no changes")
		count += 1
	else:
		diff_files = [row[0] for row in rows]
		for diff_file in diff_files:
			match = re.search(r'diff(\d+)\.json', diff_file)
			changes.append(int(match.group(1)))
		changes.sort()
	if len(changes) == 1:
		changes_gap = [changes[0]]
		average = changes[0]
		median = changes[0]
	elif len(changes) != 0:
		changes_gap = [changes[i+1] - changes[i] for i in range(len(changes)-1)]
		average = round(statistics.mean(changes_gap), 2)
		median = statistics.median(changes_gap)
	else:
		average = 0
		median = 0

	cursor.execute('''
	INSERT OR REPLACE INTO gap_table (repo_name, number_of_changes, release_gap, average, median) 
	VALUES (?, ?, ?, ?, ?)''', (repo, len(changes), str(changes_gap), average, median))

print(f"{count} repos have no changes")
conn.commit()
cursor.close()
conn.close()
