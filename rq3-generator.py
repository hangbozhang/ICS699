import csv
import re
from collections import Counter
from wordcloud import WordCloud, STOPWORDS
import sqlite3
from nltk.tokenize import word_tokenize
from nltk.util import ngrams
from nltk.stem import WordNetLemmatizer


def create_ngram(doc, n, stopword=None):
	tokens = word_tokenize(doc, language='english')
	lemmatizer = WordNetLemmatizer()  # Initialize the lemmatizer

	with open(f'{n}-tokens.txt', 'w', encoding='utf-8') as file:
		for token in tokens:
			file.write(f'{token}\n')

	# Lemmatize tokens
	lemmatized_tokens = [lemmatizer.lemmatize(word.lower(), pos='v') for word in tokens]

	filtered_token = [word for word in lemmatized_tokens if word.lower() not in stopword]

	n_grams = list(ngrams(filtered_token, n))
	ngram_counts = Counter(n_grams)
	sorted_ngrams = sorted(ngram_counts.items(), key=lambda x: x[1], reverse=True)
	# Write n-grams data to a CSV file
	with open(f'{n}gram.csv', 'w', newline='', encoding='utf-8') as csvfile:
		fieldnames = ['n-gram', 'count']
		writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

		writer.writeheader()
		for ngram, count in sorted_ngrams:
			writer.writerow({'n-gram': ' '.join(ngram), 'count': count})

	wordcloud_data = {'_'.join(ngram): count for ngram, count in sorted_ngrams}
	ngram_cloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(wordcloud_data)

	# Generate the word cloud visualization
	ngramcloud_image = ngram_cloud.to_image()

	# Display the word cloud
	ngramcloud_image.show()


# Connect to the SQLite database
conn = sqlite3.connect('SBOM')
cursor = conn.cursor()

# get notes and commit messages
cursor.execute('''SELECT release_note, commit_message FROM notes_table''')
rows = cursor.fetchall()
release_notes = [row[0] for row in rows]
commit_messages = [row[1] for row in rows]

# Combine release notes and commit messages into a single list
notes_messages_original = []
for note, message in zip(release_notes, commit_messages):
	if note is not None:
		notes_messages_original.append(note)
	if message is not None:
		notes_messages_original.append(message)

clean_list = []
url_pattern = re.compile(r'https?://\S+')
special_pattern = r'[^a-zA-Z\s]'
commit_sha_pattern = re.compile(r'[a-fA-F0-9]{5,40}')

for note in notes_messages_original:
	clean_note_without_url = url_pattern.sub(r'', note)
	clean_note_without_commit_sha = commit_sha_pattern.sub('', clean_note_without_url)
	final_clean_note = re.sub(special_pattern, ' ', clean_note_without_commit_sha)
	clean_list.append(final_clean_note)

stopwords = set(STOPWORDS)
stopwords.update([
	'github', 'http', 'https', 'commit', 'mbed', 'ARMmbed', 'BPI', 'BSP',
	'PR', 'LGTM', 'quiet', 'what', 'workflow', 'docs', 'name', 'v', 'qnames', 'readmemd', 'BabylonNative', 'Babylonjs',
	'note', 'main', 'tag', 'merge', 'greg', 'kroah', 'hartman', 'frank', 'wunderlich', 'e', 'don', 't', 'x', 'alpha',
	'electron', 'f', 'now', 's'
])

with open('message.txt', 'w', encoding='utf-8') as f:
	for message in clean_list:
		f.write(f'{message}\n')

create_ngram(' '.join(clean_list), 1, stopword=stopwords)
create_ngram(' '.join(clean_list), 2, stopword=stopwords)
create_ngram(' '.join(clean_list), 3, stopword=stopwords)
