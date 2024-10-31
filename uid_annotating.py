import pandas as pd
import csv
import json

#This script identifies unique ID for each commiter.
#Notice that path string in this script is based on initial environment of our exp. Make sure to adjust them to yours before reproduce the analysis.

csv.field_size_limit(500 * 1024 * 1024)

def data_load(PATH):
    with open(PATH, encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        commits = [row for row in reader]
    return commits

def find_id(commit, users):
    for id in users:
        for name in users[id]['names']:
            if name == commit['Author Name']:
                commit['Author Id'] = id
                return commit
    commit['Author Id'] = -1
    return commit
    assert False, "Cannot find matching Id"


# LOAD EXISTED INFO
with open('Username_info/tensorflow_after_merging.json') as user_dict:
    users = json.load(user_dict)
commits = data_load('Commits_bots_dropped/tensorflow_commit_botdropped.csv')


# REFER TO USER AND ANNOTATE
annotated_commits = []
for commit in commits:
    annotated_commit = find_id(commit, users)
    annotated_commits.append(annotated_commit)

# WRITE INTO FILES
df = pd.DataFrame(annotated_commits)
df.to_csv('Commits_with_Id/tensorflow_commit_with_Id.csv', index=False, header=True)
print('DONE')