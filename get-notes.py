import sqlite3
import requests

github_pat = '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'

base_url = "https://api.github.com/"
headers = {
	"Authorization": f'Bearer {github_pat}',
	"Accept": "application/vnd.github.v3+json"
}


def get_repo_name_owner(cursor):
	cursor.execute('''SELECT repo_name, repo_owner FROM repo_table''')
	return cursor.fetchall()


def get_tags_sha(cursor, repo_name):
	query = f'''SELECT head_tag, head_sha FROM diff_table WHERE repo_name = "{repo_name}"'''
	cursor.execute(query)
	return cursor.fetchall()


def create_notes_table(cursor):
	cursor.execute('''
		CREATE TABLE IF NOT EXISTS notes_table (
			release_tag TEXT PRIMARY KEY,
			sha TEXT,
			repo_name TEXT,
			release_note TEXT,
			commit_message TEXT
			)
	''')


def insert_notes(cursor, release_tag, sha, repo_name, release_note, commit_message):
	query = f'''INSERT OR REPLACE INTO notes_table (release_tag, sha, repo_name, release_note, commit_message)
		VALUES (?, ?, ?, ?, ?)'''
	cursor.execute(query, (release_tag, sha, repo_name, release_note, commit_message))


def main():
	# Connect to the SQLite database
	conn = sqlite3.connect('SBOM')
	cursor = conn.cursor()
	create_notes_table(cursor)

	repo_names_owners = get_repo_name_owner(cursor)

	for repo_name, repo_owner in repo_names_owners:
		tags_and_sha = get_tags_sha(cursor, repo_name)
		for head_tag, head_sha in tags_and_sha:
			head_tag_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/releases/tags/{head_tag}'

			head_tag_response = requests.get(head_tag_url, headers=headers)

			if head_tag_response.status_code == 200:
				release_note = head_tag_response.json()['body']

				commit_message_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/git/commits/{head_sha}'
				commit_message_response = requests.get(commit_message_url, headers=headers)

				if commit_message_response.status_code == 200:
					commit_message = commit_message_response.json()['message']
				else:
					print(f'Error fetching commit message for {repo_name} with tag {head_tag} sha {head_sha}. Status code: ', commit_message_response.status_code)
					break
			else:
				print(f'Error fetching release note for {repo_name} with tag {head_tag}. Status code: ', head_tag_response.status_code)
				break

			insert_notes(cursor, head_tag, head_sha, repo_name, release_note, commit_message)

	# Close the connection
	conn.commit()
	conn.close()


if __name__ == "__main__":
	main()
