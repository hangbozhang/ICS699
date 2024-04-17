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

	search_url = f"https://api.github.com/repos/{owner}/{repo}/dependency-graph/sbom"

	response = requests.get(search_url, headers=headers)

	if response.status_code == 200:
		data = response.json()

		output_file = f'{repo}_sbom.json'
		with open(output_file, "w") as file:
			json.dump(data, file, indent=4)

		print(f"SBOM was saved to {output_file}")
	else:
		print(f"Failed to retrieve SBOM. Statues code: {response.status_code}")

