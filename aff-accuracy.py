#!/usr/bin/env python3

# This python script calculates accuracy of automatically identified affiliations.

import pandas as pd
import os
import numpy as np

THRESHOLD = 5

for name_with_owner in [
    'pytorch/pytorch',
    'tensorflow/tensorflow'
    'huggingface/transformers',
]:

    df_commits = pd.read_csv(os.path.join('data_git', name_with_owner.replace('/', '_') + f'_commits_merged_{THRESHOLD}commits.csv'), index_col=0)

    for i, row in df_commits.iterrows():
        if pd.notna(row['aff_email']):
            df_commits.loc[i, 'aff'] = row['aff_email']
            df_commits.loc[i, 'ident_by'] = 'email'

    if 'sha' in df_commits.columns:
        df_commits.dropna(subset=['sha'], inplace=True)
        df_commits.set_index('sha', inplace=True)

    # df_gt is the ground truth
    df_gt = pd.read_csv(os.path.join('data_git', name_with_owner.replace('/', '_') + f'_commits_labelled_{THRESHOLD}commits.csv'), index_col=0)
    # join with ground truth
    df_join = df_commits.join(df_gt[['aff', 'ident_by']], how='inner', rsuffix='_gt')
    # replace 'Meta' -> facebook
    df_join['aff_gt'] = df_join['aff_gt'].str.replace('Meta', 'facebook')
    # convert to lowercase
    df_join['aff'] = df_join['aff'].str.lower()
    df_join['aff_gt'] = df_join['aff_gt'].str.lower()

    print(name_with_owner)
    print(sum(pd.notna(df_join['aff'])), 'of', len(df_join), 'commits have *automatically* identified affiliation')
    print(sum(pd.notna(df_join['aff_gt'])), 'of', len(df_join), 'commits have *manually* identified affiliation')
    print(sum(pd.notna(df_join['aff']) & pd.notna(df_join['aff_gt'])), 'of', sum(pd.notna(df_join['aff_gt'])), 'commits have both *automatically* and *manually* identified affiliation')

    df_join.dropna(subset=['aff_gt'], inplace=True)
    str_accuracy = lambda x, y: f"{sum(x == y)} of {len(y)}, {sum(x == y) * 100 / len(y):.2f}%"

    # calculate accuracy
    print('Accuracy:', str_accuracy(df_join['aff'], df_join['aff_gt']))
    _df = df_join[df_join['ident_by'] == 'email']
    print('Accuracy (email):', str_accuracy(_df['aff'], _df['aff_gt']))

    _df = df_join[df_join['ident_by'] == 'company_org']
    print('Accuracy (company_org):', str_accuracy(_df['aff'], _df['aff_gt']))
    print(_df[_df['aff'] != _df['aff_gt']]['aff'].value_counts()[:3])
    print(_df[_df['aff'] != _df['aff_gt']]['aff_gt'].value_counts()[:3])

    _df = df_join[df_join['ident_by'] == 'company_text']
    print('Accuracy (company_text):', str_accuracy(_df['aff'], _df['aff_gt']))

    _df = df_join[df_join['ident_by'] == 'bio_text']
    print('Accuracy (bio_text):', str_accuracy(_df['aff'], _df['aff_gt']))
    print(_df[_df['aff'] != _df['aff_gt']]['aff'].value_counts()[:3])
    print(_df[_df['aff'] != _df['aff_gt']]['aff_gt'].value_counts()[:3])