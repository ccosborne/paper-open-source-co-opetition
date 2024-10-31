#!/usr/bin/env python3

# This script collects releases and commits on GitHub.
# We tried author_email but too many commits are not associated with an email :(

import os
import github
import logging
import pandas as pd
from tqdm.auto import tqdm
from multiprocess import Pool

PROJECTS = [
    'huggingface/transformers',
    'pytorch/pytorch',
    'tensorflow/tensorflow',
]
# read github_tokens from environment variable
GITHUB_TOKENS = os.environ['GITHUB_TOKENS'].split(',')
DATA_DIR = './data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def _build_client_pool(tokens: list[str]):
    """Create a GitHub client pool to walkaround the rate limit."""
    _client_pool = []
    for t in tokens:
        auth = github.Auth.Token(t)
        gh = github.Github(auth=auth)
        try:
            print(gh.get_user().login, "*" * (len(t) - 5) + t[-5:])
            _client_pool.append(gh)
        except github.BadCredentialsException as e:
            print("Bad token", "*" * (len(t) - 5) + t[-5:], e)
            continue
    return _client_pool

client_pool = _build_client_pool(GITHUB_TOKENS)

### 1. Get releases ###

def get_repo_releases_worker(
    gh: github.Github,
    name_with_owner: str,
):
    """Get the releases of a GitHub repository."""
    repo = gh.get_repo(name_with_owner)
    _releases = []
    try:
        for r in tqdm(repo.get_releases(), desc=repo.name, total=repo.get_releases().totalCount):
            try:
                _releases.append({
                    "tag_name": r.tag_name,
                    "published_at": r.published_at,
                    "target_commit": r.target_commitish
                })
            except github.GithubException as e:
                logging.error(f"Error in {name_with_owner} {e}", exc_info=True)
                continue
        logging.info(f"Done {name_with_owner} {len(_releases)}")
        # dump to parquet
        df = pd.DataFrame(_releases)
        df.to_parquet(f"{DATA_DIR}/{name_with_owner.replace('/', '_')}_releases.parquet")
    except github.GithubException as e:
        logging.error(f"Error in {name_with_owner} {e}", exc_info=True)
        return 0
    return len(_releases)

with Pool(10) as p:
    for _ in tqdm(p.imap_unordered(
            lambda i: get_repo_releases_worker(client_pool[i % len(client_pool)], PROJECTS[i]), 
                range(len(PROJECTS)))
            , total=len(PROJECTS)):
        pass

### 2. Get commits ###

def get_commit_date(c: github.Commit.Commit):
    try:
        return c.commit.author.date
    except github.GithubException as e:
        logging.error(f"Error in commit {c.sha}: {e}")
        return None
    
def get_commit_files(c: github.Commit.Commit):
    try:
        return [x.filename for x in c.files]
    except github.GithubException as e:
        logging.error(f"Error in commit {c.sha}: {e}")
        return None

def get_repo_commits_worker(
    gh: github.Github,
    name_with_owner: str,
):
    repo = gh.get_repo(name_with_owner)
    _commits = []
    try:
        for c in tqdm(repo.get_commits(), total=repo.get_commits().totalCount, desc=repo.name):
            try:
                _commits.append({
                    "sha": c.sha,
                    "author_login": c.author.login if c.author else None,
                    "author_email": c.author.email if c.author else None,
                    "committed_at": get_commit_date(c),
                    "additions": c.stats.additions,
                    "deletions": c.stats.deletions,
                    "total": c.stats.total,
                    "files": get_commit_files(c),
                })
            except github.GithubException as e:
                logging.error(f"Error in {name_with_owner}, commit {c.sha}: {e}")
                continue
        logging.info(f"Done {name_with_owner} {len(_commits)}")
        # dump to parquet
        df = pd.DataFrame(_commits)
        df.to_parquet(f"{DATA_DIR}/{name_with_owner.replace('/', '_')}_commits.parquet")
    except github.GithubException as e:
        logging.error(f"Error in {name_with_owner} {e}", exc_info=True)
        return 0
    return len(_commits)

with Pool(10) as p:
    for _ in tqdm(p.imap_unordered(
            lambda i: get_repo_commits_worker(client_pool[i % len(client_pool)], PROJECTS[i]), 
                range(len(PROJECTS)))
            , total=len(PROJECTS)):
        pass

for p in PROJECTS:
    df = pd.read_parquet(f'./data/{p.replace("/", "_")}_commits.parquet')
    print(p, sum(df['author_login'].isna()), 'of', len(df), 'commits have no author')
    _affs = df['author_email'].dropna().apply(lambda x: x.split('@', 1)[-1]).value_counts()
    print(_affs.head(10))