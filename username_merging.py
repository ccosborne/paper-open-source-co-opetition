# coding=utf-8
import csv
import json

#This script merges different usernames of the same committer to clean up our data.

def data_load(PATH):
    with open(PATH, encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        commits = [row for row in reader]
    return commits


def reflection_build(commits):
    email_names = {}
    name_emails = {}
    for commit in commits:
        csha = commit['SHA']
        cname = commit['Committer Name']
        cemail = commit['Committer Email']
        aname = commit['Author Name']
        aemail = commit['Author Email']
        if cemail != "":
            if cemail not in email_names:
                email_names[cemail] = set()
            if cname != "":
                email_names[cemail].add(cname)
        if aemail != "":
            if aemail not in email_names:
                email_names[aemail] = set()
            if aname != "":
                email_names[aemail].add(aname)
        if cname != "":
            if cname not in name_emails:
                name_emails[cname] = set()
            if cemail != "":
                name_emails[cname].add(cemail)
        if aname != "":
            if aname not in name_emails:
                name_emails[aname] = set()
            if aemail != "":
                name_emails[aname].add(aemail)
    return email_names, name_emails


def merging(id_emails_names):
    upid = len(id_emails_names)
    iteration_time = 0
    print('Initial Nums ', len(id_emails_names))
    while True:
        iteration_time += 1
        stop = True
        for i in range(1, upid + 1):
            if i in id_emails_names:
                for j in range(i + 1, upid):
                    if j in id_emails_names and (len(id_emails_names[i][0] & id_emails_names[j][0]) > 0 or len(
                            id_emails_names[i][1] & id_emails_names[j][1]) > 0):
                        stop = False
                        id_emails_names[i][0] |= id_emails_names[j][0]
                        id_emails_names[i][1] |= id_emails_names[j][1]
                        del id_emails_names[j]
        l = len(id_emails_names)
        print('After the {} iteration, remain {}'.format(iteration_time, l))
        if stop:
            break
    merged_num = upid - len(id_emails_names)
    return id_emails_names, merged_num


def format_res(id_emails_names):
    users = {}
    real_id = 1
    for id in id_emails_names:
        user_info = {}
        user_info['emails'] = list(id_emails_names[id][0])
        user_info['names'] = list(id_emails_names[id][1])
        users[real_id] = user_info
        real_id += 1
    return users


if __name__ == '__main__':
    id_emails_names = {}
    id_names_emails = {}
    
    # change to PATH to the real path on your device
    PATH = 'Commits_bots_dropped/pytorch_commit_botdropped.csv'
    csv.field_size_limit(500 * 1024 * 1024)

    commits = data_load(PATH)
    email_names, name_emails = reflection_build(commits)

    id = 1
    _id = 1
    for email in email_names:
        id_emails_names[id] = [{email}, email_names[email]]
        id += 1

    users = format_res(id_emails_names)
    original_num = len(users)
    
    PATH = 'username_info/pytorch_before_merging.json'
    with open(PATH, 'w') as f: 
        json.dump(users, f)

    for name in name_emails:
        id_emails_names[id] = [name_emails[name], {name}]
        id_names_emails[_id] = [{name}, name_emails[name]]
        _id += 1

    id_emails_names, merged_num = merging(id_emails_names)

    users = format_res(id_emails_names)
    res_num = len(users)
    PATH = 'username_info/pytorch_after_merging.json'
    with open(PATH, 'w') as f:
        json.dump(users, f)

    print('======USERNAME MERGING DONE======')
    print('{} in total, merged {}, remain {}'.format(original_num, original_num - res_num, res_num))

