import csv
import sqlite3
import numpy as np
from scipy.stats import iqr


def calculate_summary(data, column_name, print_summary=True):
	q1 = np.percentile(data, 25)
	q3 = np.percentile(data, 75)
	iqr_value = iqr(data)
	lower_bound = q1 - 1.5 * iqr_value
	upper_bound = q3 + 1.5 * iqr_value

	if print_summary:
		# Print values for debugging
		print(f"Data: {data}")
		print(f"Count: {len(data)}")
		print(f"Q1: {q1}, Q3: {q3}, IQR: {iqr_value}")
		print(f"Lower Bound: {lower_bound}, Upper Bound: {upper_bound}")

	# Filter out outliers
	filtered_data = [value for value in data if lower_bound <= value <= upper_bound]

	count = len(filtered_data)
	mean_value = np.mean(filtered_data)
	std_dev = np.std(filtered_data)
	minimum = np.min(filtered_data)
	q1_filtered = np.percentile(filtered_data, 25)
	median_filtered = np.median(filtered_data)
	q3_filtered = np.percentile(filtered_data, 75)
	maximum = np.max(filtered_data)
	iqr_value_filtered = iqr(filtered_data)

	if print_summary:
		print("\nDetailed Summary for {}:".format(column_name))
		print(f"Count: {count}")
		print(f"Mean: {mean_value}")
		print(f"Std Dev: {std_dev}")
		print(f"Min: {minimum}")
		print(f"Q1: {q1_filtered}")
		print(f"Median (Q2): {median_filtered}")
		print(f"Q3: {q3_filtered}")
		print(f"Max: {maximum}")
		print(f"IQR: {iqr_value_filtered}")
		print()

	return [count, mean_value, std_dev, minimum, q1_filtered, median_filtered, q3_filtered, maximum, iqr_value_filtered]


def five_number_summary(data, name):
	five_summary = np.percentile(data, [0, 25, 50, 75, 100])

	print(f"5-Number Summary for {name}:")
	print(f"Count: {len(data)}")
	print(f"Minimum: {five_summary[0]}")
	print(f"Q1: {five_summary[1]}")
	print(f"Median (Q2): {five_summary[2]}")
	print(f"Q3: {five_summary[3]}")
	print(f"Maximum: {five_summary[4]}")
	print(f"Mean: {np.mean(data)}")
	print()


# Connect to the SQLite database
conn = sqlite3.connect('SBOM')
cursor = conn.cursor()

# Fetch the data from the gap_table
cursor.execute('''SELECT number_of_changes, release_gap, repo_name FROM gap_table''')
rows = cursor.fetchall()

# Extract the columns
number_of_changes = [row[0] for row in rows]
release_gap_values = [eval(row[1]) if row[1] else [] for row in rows]  # Handle empty release_gap
repo_names = [row[2] for row in rows]

conn.close()

# Check for empty lists
# if not number_of_changes or not any(release_gap_values):
# print("No data available.")

# else:
# Calculate 5-number summary for number_of_changes
five_number_summary(number_of_changes, 'number_of_changes')

# Filter out zeros from number_of_changes
non_zero_number_of_changes = [value for value in number_of_changes if value != 0]
non_zero_repo_names = [repo_name for value, repo_name in zip(number_of_changes, repo_names) if value != 0]

five_number_summary(non_zero_number_of_changes, 'number_of_changes')

calculate_summary(non_zero_number_of_changes, 'number_of_changes')

# Calculate 5-number summary for each row of release_gap
release_gap_summaries = [
	np.percentile(row, [0, 25, 50, 75, 100]) if isinstance(row, list) and row else [np.nan, np.nan, np.nan, np.nan, np.nan]
	for row in release_gap_values
]

# Specify the CSV file name
csv_filename = 'summaries.csv'

# Open the CSV file for writing
with open(csv_filename, 'w', newline='') as csvfile:
	# Create a CSV writer
	csv_writer = csv.writer(csvfile)

	# Write header row
	csv_writer.writerow(['Repo Name', 'Count', 'Mean', 'Std Dev', 'Min', 'Q1', 'Median (Q2)', 'Q3', 'Max', 'IQR'])

	# Write summaries for each row
	for repo_name, summary in zip(repo_names, release_gap_summaries):
		if not any(np.isnan(summary)):  # Check for non-null values
			row_summary = calculate_summary(summary, 'release_gap', False)
			csv_writer.writerow([repo_name] + row_summary)

	print(f"Summaries for each row have been written to {csv_filename}")

# Calculate 5-number summary for the entire column of release_gap
all_release_gap_values = [value for row_values in release_gap_values if isinstance(row_values, list) for value in row_values]
five_number_summary(all_release_gap_values, 'release_gap')

if all_release_gap_values:  # Check for non-empty values
	calculate_summary(all_release_gap_values, 'release_gap')

# Perform Tukey's HSD test on the filtered data for number_of_changes
# df_filtered = pd.DataFrame({'number_of_changes': non_zero_number_of_changes, 'repo_name': non_zero_repo_names})
# anova_result_filtered = df_filtered.groupby('repo_name')['number_of_changes'].apply(list)

# mc_filtered = MultiComparison(df_filtered['number_of_changes'], df_filtered['repo_name'])
# result_filtered = mc_filtered.tukeyhsd()

# print(result_filtered)
