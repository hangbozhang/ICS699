import csv
import os
import requests
import json

github_pat = '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'

base_url = "https://api.github.com/"
headers = {
	"Authorization": f'Bearer {github_pat}',
	"Accept": "application/vnd.github.v3+json"
}


while True:
	repo_url = input("Enter the repo URL (or type exit to stop): ")

	if repo_url.lower() == 'exit':
		break

	name_split = repo_url.split('/')

	if len(name_split) < 2:
		print("Invalid URL.")
		continue

	owner = name_split[-2]
	repo = name_split[-1]

	page = 1
	commit_shas = []
	commit_dates = []

	directory_path = f"{repo}"
	# Get the current directory of Python script
	script_directory = os.path.dirname(os.path.abspath(__file__))
	# Combine the script directory and the destination directory to create the full destination path
	full_destination_path = os.path.join(script_directory, directory_path)
	# Ensure the directory exists; if not, create it
	if not os.path.exists(full_destination_path):
		os.makedirs(full_destination_path)

	sha_file = f'{repo}_sha.csv'
	full_sha_file_path = os.path.join(full_destination_path, sha_file)

	with open(full_sha_file_path, 'w', newline='') as file:
		writer = csv.writer(file)
		writer.writerow(["Base", "Head", "Filename", "Base Commit Date", "Head Commit Date"])

		while True:
			commits_url = f"https://api.github.com/repos/{owner}/{repo}/commits?page={page}"
			commits_response = requests.get(commits_url, headers=headers)

			if commits_response.status_code == 200:
				commits_detail = commits_response.json()
				# get all commit sha
				if commits_detail:
					for commit in commits_detail:
						commit_sha = commit['sha']
						commit_date = commit['commit']['committer']['date']
						commit_shas.append(commit_sha)
						commit_dates.append(commit_date)

					print('fetching page ', page)
					page += 1
					if page == 11:
						break
				else:
					break
			else:
				print('Error fetching releases. Status code: ', commits_response.status_code)
				break

		for i in range(len(commit_shas)):
			if i == len(commit_shas) - 1:
				break
			base_commit_sha = commit_shas[i + 1]
			base_commit_date = commit_dates[i + 1]
			head_commit_sha = commit_shas[i]
			head_commit_date = commit_dates[i]
			compare_url = \
				f"https://api.github.com/repos/{owner}/{repo}/dependency-graph/compare/{base_commit_sha}...{head_commit_sha}"
			print('---------------------------------------------------------------')
			print(f'base commit sha is: {base_commit_sha}  |\nhead commit sha is: {head_commit_sha}  |')

			response = requests.get(compare_url, headers=headers)

			if response.status_code == 200:
				sbom_diff = response.json()
				if sbom_diff:
					output_file = f'{repo}_diff{i}.json'
					full_output_file_path = os.path.join(full_destination_path, output_file)
					with open(full_output_file_path, "w") as f:
						json.dump(sbom_diff, f, indent=4)

					writer.writerow([base_commit_sha, head_commit_sha, output_file, base_commit_date, head_commit_date])
					print(f"| ********** SBOM diff was saved to {output_file} *********  |")
					print('---------------------------------------------------------------\n')
				else:
					print("| #############  Skipped as no change was made #############  |")
					print('---------------------------------------------------------------\n')
			else:
				print(f"Failed to retrieve SBOM. Statues code: {response.status_code}")
