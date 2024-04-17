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

repo_urls = []

with open('result2.csv', 'r') as csv_file:
	reader = csv.reader(csv_file)
	for row in reader:
		repo_urls.append(row[0])

for repo_url in repo_urls:
	name_split = repo_url.split('/')

	if len(name_split) < 2:
		print("Invalid URL.")
		continue

	owner = name_split[-2]
	repo = name_split[-1]

	print(f"Processing {repo_url}, all files will be stored in {repo} directory.")

	page = 1
	tag_data = {}
	commit_sha = []
	all_tag_name = []
	tag_date = []

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
		writer.writerow(["Base", "Head", "Filename", "Base Tag", "Base Date", "Head Tag", "Head Date"])

		while True:
			refs_url = f"https://api.github.com/repos/{owner}/{repo}/releases?page={page}"
			refs_response = requests.get(refs_url, headers=headers)

			if refs_response.status_code == 200:
				releases = refs_response.json()
				# get all tag names
				if releases:
					for release in releases:
						tag_name = release['tag_name']
						tag_sha = ""
						release_date = release['published_at']

						tag_data[tag_name] = {
							"tag_sha": tag_sha,
							"tag_date": release_date,
							"commit_sha": "",
						}

					print('fetching page ', page)
					page += 1
				else:
					break
			else:
				print('Error fetching releases. Status code: ', refs_response.status_code)
				break
		# get all commit sha
		for tag_name in tag_data:
			tag_url = f'https://api.github.com/repos/{owner}/{repo}/git/refs/tags/{tag_name}'

			tag_response = requests.get(tag_url, headers=headers)

			if tag_response.status_code == 200:
				tag_details = tag_response.json()
				# get the sha of the tags
				if tag_details['object']['type'] == 'tag':
					tag_sha = tag_details['object']['sha']
					tag_data[tag_name]['tag_sha'] = tag_sha
				# using the tag sha to get the commit sha
					sha_url = f'https://api.github.com/repos/{owner}/{repo}/git/tags/{tag_sha}'

					sha_response = requests.get(sha_url, headers=headers)
					if sha_response.status_code == 200:
						sha_detail = sha_response.json()
						commit_sha.append(sha_detail['object']['sha'])
						tag_data[tag_name]['commit_sha'] = sha_detail['object']['sha']
						tag_date.append(sha_detail['tagger']['date'])
						tag_data[tag_name]['tag_date'] = sha_detail['tagger']['date']
						print('fetching commit SHA for ', tag_name, 'date is ', sha_detail['tagger']['date'])
					else:
						print('Fail to fetch commit sha. Status code: ', sha_response.status_code, tag_name)
						break
				elif tag_details['object']['type'] == 'commit':
					commit_sha.append(tag_details['object']['sha'])
					tag_data[tag_name]['commit_sha'] = tag_details['object']['sha']
					print('fetching commit SHA for ', tag_name, 'date is ', tag_data[tag_name]['tag_date'])
			else:
				print('Fail to fetch tag sha. Status code: ', tag_response.status_code)
				break
		i = 0
		for tag_name in tag_data:
			base_commit_sha = tag_data[tag_name]['commit_sha']

			next_tag_name = list(tag_data)[list(tag_data).index(tag_name) - 1]
			head_commit_sha = tag_data[next_tag_name]['commit_sha']
			compare_url = \
				f"https://api.github.com/repos/{owner}/{repo}/dependency-graph/compare/{base_commit_sha}...{head_commit_sha}"
			print(f'base commit sha is: {base_commit_sha}, head commit sha is: {head_commit_sha}')

			response = requests.get(compare_url, headers=headers)

			if response.status_code == 200:
				sbom_diff = response.json()
				if sbom_diff:
					output_file = f'{repo}_diff{i}.json'
					full_output_file_path = os.path.join(full_destination_path, output_file)
					with open(full_output_file_path, "w") as f:
						json.dump(sbom_diff, f, indent=4)

					writer.writerow([base_commit_sha, head_commit_sha, output_file, tag_name, tag_data[tag_name]['tag_date'], next_tag_name, tag_data[next_tag_name]['tag_date']])
					print(f"SBOM diff was saved to {output_file}")
				else:
					print("Skipped as no change was made.")
			else:
				print(f"Failed to retrieve SBOM. Statues code: {response.status_code}")
			i += 1
