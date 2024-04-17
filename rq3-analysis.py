from top2vec import Top2Vec
import sqlite3
import os

# Connect to the SQLite database
conn = sqlite3.connect('SBOM')
cursor = conn.cursor()

# get notes and commit messages
cursor.execute('''SELECT release_note, commit_message FROM notes_table''')
rows = cursor.fetchall()
release_notes = [row[0] for row in rows]
commit_messages = [row[1] for row in rows]

# Check for non-string values in release_notes
# for note in release_notes:
# 	if not isinstance(note, str):
# 		print(f"Found non-string value in release_notes: {note}")

# Check for non-string values in commit_messages
# for message in commit_messages:
# 	if not isinstance(message, str):
# 		print(f"Found non-string value in commit_messages: {message}")

# Combine release notes and commit messages into a single list
notes_messages_original = []
for note, message in zip(release_notes, commit_messages):
	if note is not None:
		notes_messages_original.append(note)
	if message is not None:
		notes_messages_original.append(message)

filename = "top2vec_model"

if os.path.exists(filename):
	model = Top2Vec.load(filename)
else:
	# Initialize and fit Top2Vec model
	model = Top2Vec(
		notes_messages_original,
		embedding_model="doc2vec",
		speed="fast-learn",
		workers=8,
		hdbscan_args={"min_cluster_size": 65, "min_samples": 10},
	)

	# model.save(filename)

total = model.get_num_topics()

topic_words, word_scores, topic_nums = model.get_topics(total)

# Print topics
for topic_id, topic_words in enumerate(topic_words):
	print(f"Topic {topic_id}: {', '.join(topic_words[:3])}")

doc, doc_scores, doc_ids = model.search_documents_by_topic(topic_num=3, num_docs=5)
for doc, score, doc_id in zip(doc, doc_scores, doc_ids):
	print(f"Document: {doc_id}, Score: {score}")
	print("-----------")
	print(doc)
	print("-----------")
	print()
