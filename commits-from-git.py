#!/usr/bin/env python3

# This script collects commits and identifies the affiliations by git commit history.
# Clear that we are missing a lot of the author information by querying GitHub API.
# The commits with no associated authors are mostly from internal git accounts, e.g. abodrov@yandex-team.ru.

import pandas as pd
import git
import os
import shutil
from tqdm import tqdm
from multiprocess import Pool
from typing import Literal
from datetime import datetime, tzinfo
import pytz
import pydriller
import json

# the list of projects to analyze
PROJECTS = [
    'huggingface/transformers',
    'pytorch/pytorch',
    'tensorflow/tensorflow',
]

### 1. Clone repos ###

def clone_repository(
    name_with_owner: str,
    base_path: str = 'repo',
    if_exists: Literal['overwrite', 'update', 'ignore'] = 'ignore',
):
    """Clone a Git repository to a local directory."""
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    _dest_path = os.path.join(base_path, name_with_owner.replace("/", "_"))
    
    if os.path.exists(_dest_path):
        if if_exists == 'overwrite':
            shutil.rmtree(_dest_path)
        elif if_exists == 'update':
            repo = git.Repo(_dest_path)
            repo.remotes.origin.pull()
            return _dest_path
        else:
            return _dest_path
    
    repo = git.Repo.clone_from(f"git@github.com:{name_with_owner}.git", _dest_path)
    return _dest_path

with Pool(len(PROJECTS)) as pool:
    for _ in tqdm(pool.imap_unordered(clone_repository, PROJECTS), total=len(PROJECTS)):
        pass

### 2. Analyze commits ###

# pytorch's donation to linux foundation
CUTOFF_DATE = datetime(2022, 9, 12, tzinfo=pytz.UTC)

# the most exhaustive list of email domains
# https://gist.github.com/ammarshah/f5c2624d767f91a7cbdc4e54db8dd0bf
with open('public_email_domains.txt', 'r') as f:
    PUBLIC_EMAIL_DOMAINS = set(f.read().splitlines())
    PUBLIC_EMAIL_DOMAINS.add('users.noreply.github.com')

def is_corporate_domain(domain: str | None):
    """Check if a email address is corporate email."""
    if domain in PUBLIC_EMAIL_DOMAINS or domain is None:
        return False
    # it's very hard to tell if a domain is corporate or not,
    # e.g. .com .co .ai .io .com.* .co.*
    for pat in '.com', '.io', '.ai', '.co':
        if pat in domain:
            return True
    return False

def get_file_stats(commit: pydriller.Commit):
    """Calculate the number of lines added, deleted, and modified to a file."""
    _res = {}
    for f in commit.modified_files:
        _res[f.new_path] = {
            "add": f.added_lines,
            "del": f.deleted_lines,
            "sum": f.added_lines + f.deleted_lines,
        }
    return _res

def count_commits(repo_path):
    """Count the number of commits in a Git repository."""
    repo = git.Repo(repo_path)
    return int(repo.git.rev_list('--all', '--count'))

def update_author_aff(author: str, email: str, aff_dict: dict[str, str | None]):
    """Get and update the author's affiliation.
    The user's affiliation is determined by the last known corporate email.
    This walk around the threats of joining a new company and changing the email.
    """
    _aff = email.split("@")[-1] if email else None
    if not is_corporate_domain(_aff):
        return aff_dict.get(author.lower(), None)
    else:
        aff_dict[author.lower()] = _aff
        return _aff

def build_commits_dataset(
    name_with_owner: str,
    base_path: str,
    cutoff_date: datetime,
):
    """Build a dataset of commits for a repository."""
    _df_commits = pd.DataFrame(
        columns=["sha", "date", "name", "email", "files", "files_cnt", "add", "del", "sum", "aff"],
    )
    _df_commits.set_index("sha", inplace=True)

    _author_aff = {}

    _dest_path = os.path.join(base_path, name_with_owner.replace("/", "_"))
    _total = count_commits(_dest_path)
    repo = pydriller.Repository(_dest_path,to=cutoff_date)
    # by default, pydriller traveses the whole history of the repo, by ascending order of commit time
    for cmt in tqdm(repo.traverse_commits(), total=_total, desc=name_with_owner):
        _df_commits.loc[cmt.hash] = [
            cmt.author_date,
            cmt.author.name,
            cmt.author.email,
            get_file_stats(cmt),
            len(cmt.modified_files),
            cmt.insertions,
            cmt.deletions,
            cmt.lines,
            update_author_aff(cmt.author.name, cmt.author.email, _author_aff),
        ]

    # count commits by author
    _df_vc = pd.DataFrame(_df_commits['name'].str.lower().value_counts())
    _df_vc.columns = ['commits_cnt']
    # map author to affiliation
    _df_vc['aff'] = _df_vc.index.map(_author_aff)

    # print the percentage of users without affiliation
    print(f"{name_with_owner}: {sum(_df_vc['aff'].isna())} of {_df_vc.shape[0]} authors have no affiliation")
    _df_vc_10cmt = _df_vc[_df_vc['commits_cnt'] >= 10]
    print(f"{name_with_owner}: {sum(_df_vc_10cmt['aff'].isna())} of {_df_vc_10cmt.shape[0]} authors with >= 10 commits have no affiliation")

    return _df_commits, _df_vc

def worker(name_with_owner: str):
    _df, _vc = build_commits_dataset(name_with_owner, base_path='repo', cutoff_date=CUTOFF_DATE)
    os.makedirs('data_git', exist_ok=True)
    _df.to_csv(f'data_git/{name_with_owner.replace("/", "_")}_commits.csv')
    _vc.to_csv(f'data_git/{name_with_owner.replace("/", "_")}_vc.csv')

with Pool(len(PROJECTS)) as pool:
    for _ in pool.imap_unordered(worker, PROJECTS):
        pass

### 3. Filtering out commits ###

with open("bots.json", "r") as f:
    jb = json.load(f)
    li = []
    for k, v in jb.items():
        li.extend(v)
    BOTS = set(li)

THRESHOLD = 5  # only keeping users with >=X commits

for p in PROJECTS:
    _df = pd.read_csv(f"data_git/{p.replace('/', '_')}_commits.csv")
    _vc = pd.read_csv(f"data_git/{p.replace('/', '_')}_vc.csv")
    # drop bots
    _vc = _vc[~_vc['name'].isin(BOTS)]
    print(p)
    print(sum(_vc['aff'].isna()), 'of', _vc.shape[0], 'authors have no affiliation')
    _vc_filtered = _vc[_vc['commits_cnt'] >= THRESHOLD]
    print(sum(_vc_filtered['aff'].isna()), 
          'of', _vc_filtered.shape[0], 
          f'authors with >= {THRESHOLD} commits have no affiliation')
    # report percentiles
    print(_vc['commits_cnt'].describe(percentiles=[ .75, .90, .95, .99]))
    # dump to csv
    _vc_filtered.to_csv(f'data_git/{p.replace("/", "_")}_vc_filtered.csv')
    _df_filtered = _df[_df['name'].isin(_vc_filtered['name'])]
    _df_filtered.to_csv(f'data_git/{p.replace("/", "_")}_commits_filtered.csv')
    print(len(_df_filtered), 'commits left')