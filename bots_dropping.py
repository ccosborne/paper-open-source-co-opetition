import csv
import pandas as pd
import json

#This script drops commits made by bots to clean up the source data.
#Notice that path string in this script is based on initial environment of our exp. Make sure to adjust them to yours before reproduce the analysis.

with open("bots.json", "r") as f:
    bot_dict = json.load(f)

csv.field_size_limit(500 * 1024 * 1024)

# Function: TO Analyse the committers' INFO
def committer_summary(commits):
    committers = {}
    for idx in range(len(commits)):
        committer_name = commits[idx]['Committer Name']
        if committer_name not in committers:
            committer_info = {}
            committer_info['commit_num'] = 1
            committer_info['email_add'] = commits[idx]['Committer Email']
            committers[committer_name] = committer_info
        else:
            committers[committer_name]['commit_num'] += 1
    print('Committer_nums: ', len(committers))
    file_path = 'transformers_committers_info.json'
    with open(file_path, 'w') as f:
        json.dump(committers, f)


dropped_names = {}
author_names= {}
dropping_idx = []
filename = "Commit/transformers_commit_data.csv"
# filename = "Commit/pytorch_commit_data.csv"
with open(filename, encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    count = 0
    commits = [row for row in reader]
original_num = len(commits)


committer_summary(commits)


# Start Checking
for idx in range(original_num):
    flag = 0
    for name in bot_dict["huggingface/transformers"]:
        if flag:
            break
        if name in commits[idx]['Login Name']:
            flag += 1
            if name not in dropped_names:
                dropped_names[name] = 1
            else:
                dropped_names[name] += 1
            dropping_idx.append(idx)
        elif commits[idx]['Login Name'] == '':
            print(commits[idx]['Author Name'], ' ', commits[idx]['Author Email'])
            if name in commits[idx]['Author Name']:
                flag += 1
                dict_name = 'BLANK_LOGIN_WITH_AUTHOR:' + name
                if dict_name not in dropped_names:
                    dropped_names[dict_name] = 1
                else:
                    dropped_names[dict_name] += 1
                dropping_idx.append(idx)

    # Record Valid Users
    if not flag:
        if commits[idx]['Author Name'] not in author_names:
            author_names[commits[idx]['Author Name']] = 1
        else:
            author_names[commits[idx]['Author Name']] += 1


# Dropping
for idx in reversed(dropping_idx):
    commits.pop(idx)
final_num = len(commits)


# Record Results
df = pd.DataFrame(commits)
df.to_csv('transformers_commit_botdropped.csv', index=False, header=True)


# Print Results
print('====== BOTS DROPPING DONE ======')
print(dropped_names)
print('Origin:{}, Final:{}, Dropped:{}, Dropping_Percentage:{}'.format(original_num, final_num, len(dropping_idx), (original_num-final_num)/original_num))
print(author_names)
print(len(author_names))