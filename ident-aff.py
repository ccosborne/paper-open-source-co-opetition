#!/usr/bin/env python3

# This script identifies affiliation of users with all available information.

from ast import Tuple
import pandas as pd
import os
import numpy as np
import random
from datetime import datetime
import pytz
import json
import re
from pprint import pprint
from typing import Union, Literal, Tuple
from tqdm.auto import tqdm

PROJECTS = [
    'huggingface/transformers',
    'pytorch/pytorch',
    'tensorflow/tensorflow',
]

RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# Only users with >=X commits
THRESHOLD = 5

# pytorch's donation to linux foundation
CUTOFF_DATE = datetime(2022, 9, 12, tzinfo=pytz.UTC)

# bots list
with open("bots.json", "r") as f:
    jb = json.load(f)
    li = []
    for k, v in jb.items():
        li.extend(v)
    BOTS = set(li)

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

with open('company_ident_patterns.json', 'r') as f:
    COMPANY_PATTERNS = json.load(f)
# some companies have multiple domains
COMPANY_EMAIL_MAP = {
    'fb.com': 'facebook',
}
COMPANY_ORG_PATTERN = re.compile(r'@([a-zA-Z0-9\-_]+)')

def infer_aff_from_email(
    email: Union[str, None],
):
    """Infers user's affiliation by email"""
    if not email or pd.isna(email):
        return None
    _email_aff = email.lower().split('@')[-1]
    if not is_corporate_domain(_email_aff):
        return None
    if _email_aff in COMPANY_EMAIL_MAP:
        return COMPANY_EMAIL_MAP[_email_aff]
    _split = _email_aff.split('.')
    if _split[-2] in ('com', 'co'):  # .co.in, .com.cn
        return _split[-3]  
    else:
        return _split[-2]
    
def infer_user_aff(row) -> Union[Tuple[str, str], Tuple[None, None]]:
    """Infer user's affiliation from email, company name, and more."""
    if pd.isna(row['Author Email']):
        return None, None
    _email_aff = row['Author Email'].split('@')[-1] if row['Author Email'] else None
    if not _email_aff and row['Login Email']:
        _email_aff = row['Login Email'].split('@')[-1]
    _aff = infer_aff_from_email(_email_aff)
    if _aff:
        return _aff, 'email'
    
    # find org references in 'Author Company', e.g. @google
    if not pd.isna(row['Author Company']):
        _orgs = COMPANY_ORG_PATTERN.findall(row['Author Company'])
        if _orgs:
            return ','.join(_orgs), 'company_org'  # @tensorflow, @google

    # match natural language patterns, e.g. Work at Google
    for _ident_by, _text in ('company_text', row['Author Company']), ('bio_text', row['Author Bio']):  # Company is always over Bio
        if pd.isna(_text):
            continue
        _text = _text.lower()
        # remove special characters
        _text = _text.replace('.', ' ').replace(',', ' ').replace(';', ' ').replace(':', ' ')
        # try to match
        for _pat, _aff in COMPANY_PATTERNS.items():
            if _pat in _text:
                return _aff, _ident_by
    
    return None, None


for name_with_owner in PROJECTS:
    df_commits_info = pd.read_csv(os.path.join('Commits_with_Id', name_with_owner.split('/')[-1] + '_commit_with_Id.csv'))

    with open(os.path.join('Username_info', name_with_owner.split('/')[-1] + '_after_merging.json')) as f:
        _obj = json.load(f)
    _email_to_id = {}
    _name_to_id = {}
    for _id, _v in _obj.items():
        for em in _v["emails"]:
            _email_to_id[em] = int(_id)
        for name in _v["names"]:
            _name_to_id[name.lower()] = int(_id)

    def get_user_id(row):
        _email = row['Author Email']
        if not pd.isna(_email):
            if _email in _email_to_id:
                return _email_to_id[_email]
        _name = row['Author Name']
        if not pd.isna(_name):
            _name = _name.lower()
            if _name in _name_to_id:
                return _name_to_id[_name]
        return None

    df_authors = pd.DataFrame(
        columns=['login', 'name', 'email', 'company', 'location', 'bio', 'twitter', 'id', 'aff', 'ident_by'],
    )
    df_authors.set_index('login', inplace=True)

    # 1. Identify affiliations
    for idx, row in tqdm(df_commits_info.iterrows(), total=len(df_commits_info)):
        _name = row['Author Name']
        _email = row['Author Email'] if pd.notna(row['Author Email']) else row['Login Email']

        _login = row['Login Name']
        if pd.isna(_login):
            _login = _email  # special case for unmatched users

        _company = row['Author Company']
        _location = row['Author Location']
        _bio = row['Author Bio']
        _twitter = row['Author Twitter Username']
        _id = get_user_id(row)
        _aff, _ident_by = infer_user_aff(row)
        df_authors.loc[_login] = (_name, _email, _company, _location, _bio, _twitter, _id, _aff, _ident_by)

    def apply_wrapper(df: pd.DataFrame):
        _df_dropna = df['aff'].dropna()
        if _df_dropna.empty:
            return df
        _first_aff = _df_dropna.iloc[0]
        for idx in df[df['aff'].isna()].index:
            print(idx, _first_aff)
            df_authors.loc[idx, 'aff'] = _first_aff
            df_authors.loc[idx, 'ident_by'] = 'merged'

    _df_duplicates = df_authors[df_authors['id'].duplicated(keep=False)].sort_values('id')
    _df_duplicates.groupby('id').apply(apply_wrapper)
    _df_duplicates = df_authors[df_authors['id'].duplicated(keep=False)].sort_values('id')
    print("Duplicates:", _df_duplicates)
    _has_company = df_authors['company'].notna()
    _no_aff = df_authors['aff'].isna()
    print("Failed to ident:", df_authors[(_has_company) & _no_aff & df_authors['company'].str.contains('@', case=False)])

    # 2. Remove bots
    dict_login_to_id = df_authors['id'].to_dict()
    bots_id = set()
    for _login in BOTS:
        if _login in dict_login_to_id:
            bots_id.add(dict_login_to_id[_login])

    df_commits = pd.read_csv(f"data_git/{name_with_owner.replace('/', '_')}_commits.csv")
    df_commits['Author Name'] = df_commits['name']
    df_commits['Author Email'] = df_commits['email']
    df_commits['author_id'] = df_commits.apply(get_user_id, axis=1)  # user with an ID can be a bot
    df_no_bot = df_commits[df_commits['sha'].isin(df_commits_info['SHA'])]  
    df_no_bot.drop(columns=['Author Name', 'Author Email'], inplace=True)
    df_no_bot[df_no_bot['author_id'].isna()]

    print(sum(df_no_bot['author_id'].isna()), "commits without user id are removed")
    df_no_bot.dropna(subset=['author_id'], inplace=True)
    df_no_bot['author_id'] = df_no_bot['author_id'].astype(int)
    
    df_join = df_no_bot.rename(columns={'aff':'aff_email'})\
        .merge(pd.DataFrame(df_authors[['id', 'aff', 'ident_by']].groupby('id').first()),
            left_on='author_id', right_on='id', how='left')
    df_join.to_csv(os.path.join('data_git', name_with_owner.replace('/', '_') + '_commits_merged.csv'))

    # 3. Log cases where aff identified by email != aff identified with all info
    # Save for manual inspection
    df_inconsistent = df_join[df_join['aff_email'].notna() & df_join['aff'].notna() & (df_join['aff_email'] != df_join['aff'])]
    df_inconsistent = df_commits[df_commits['sha'].isin(df_inconsistent['sha'])]
    df_inconsistent.sort_values('author_id', inplace=True)
    df_inconsistent = df_inconsistent[['author_id'] + list(df_inconsistent.columns[:-3]) + list(df_inconsistent.columns[-2:])]
    df_inconsistent.to_csv(os.path.join('data_git', name_with_owner.replace('/', '_') + f'_commits_merged_{THRESHOLD}commits_inconsistent.csv'))

    # Email aff should override user aff
    df_join['aff_email'] = df_join['aff_email'].apply(infer_aff_from_email)
    df_join['aff'] = df_join['aff'].str.lower()

    # 4. Print stats
    print('>>>', name_with_owner)
    print(sum(df_authors['aff'].isna()), 'of', df_authors.shape[0], 'authors have no affiliation')
    _vc = df_join['author_id'].value_counts()
    print(_vc.describe(percentiles=[ .75, .90, .95, .99]))
    _freq_user_ids  = _vc[_vc >= THRESHOLD].index
    print(sum(df_join['author_id'].isin(_freq_user_ids)), 'of', len(df_join['author_id']), 'commits are from frequent authors')
    df_freq = df_authors[df_authors['id'].isin(_freq_user_ids)]
    df_freq['commits'] = df_freq['id'].map(_vc)
    df_freq.sort_values('commits', ascending=False, inplace=True)
    df_freq.to_csv(os.path.join('data_git', name_with_owner.replace('/', '_') + f'_authors_merged_{THRESHOLD}commits.csv'))
    print(sum(df_freq['aff'].isna()), 'of', len(_freq_user_ids), 'authors have >=', THRESHOLD, 'commits', 'have no affiliation')
    df_commits = df_join[df_join['author_id'].isin(_freq_user_ids)]
    df_commits.to_csv(os.path.join('data_git', name_with_owner.replace('/', '_') + f'_commits_merged_{THRESHOLD}commits.csv'))
