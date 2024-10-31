# Overview

This repository contains Python scripts used for a research paper on open source co-opetition (preprint: https://arxiv.org/abs/2410.18241). The scripts enable the collection of historical commit data from GitHub repositories via the GitHub REST API, the analysis of code authorship at the company-level, and the construction of edgelists for commit-based collaboration networks. 


## Scripts for Mining Software Repositories and Authorship Analysis

The scripts collect historical commit data from GitHub repositories via the GitHub REST API. For each repository commit, the scripts collect comprehensive metadata including the commit SHA, date, author name, email address, modified source files, and lines of code (LOC) metrics covering additions, deletions, and net changes.

### Data Processing Scripts

The analysis pipeline encompasses several data processing components. The username merging system addresses the common challenge of multiple identities for unique developers—a frequent occurrence when developers utilise multiple GitHub accounts or varying Git credentials. This system constructs bipartite networks that map usernames to their corresponding email addresses and vice versa, enabling identity merging based on these linked pairs. Each merged identity receives a unique identifier for subsequent analysis.

Following established practices in software engineering research, the bot filtering script removes bot-generated commits from datasets. This ensures the analysis focuses solely on human contributions by identifying and filtering out automated commit patterns.

### Affiliation Identification

The affiliation identification script employs a semi-automated approach to determine contributors' organisational affiliations at the time of each commit. It first mines affiliations from commit email addresses, which typically provide the most reliable source of affiliation data. Consumer email addresses, identified using a publicly available list, are excluded from this initial identification.

For contributors with missing affiliations, the script mines GitHub profile data, focusing on users with five or more commits to maintain data quality. Contributors without company affiliations are classified as "volunteers", whilst unidentifiable affiliations are marked as "unknown". In cases where contributors use both company and private email addresses, the script associates all commits with their company affiliation.

### Input Requirements

- GitHub repository URL
- GitHub API authentication credentials
- List of known consumer email domains
- Minimum commit threshold (default: 5)

### Output

The scripts generate processed datasets containing:
- Merged user identities
- Filtered commit history (bots removed)
- Contributor affiliation data
- Validation statistics


## Scripts for Network Analysis of Commit-based Collaboration
This repository contains Python scripts that generate directed network edge lists representing developer collaboration patterns based on shared file modifications between software releases. The scripts analyse commit patterns and construct networks where edges represent shared file touches between developers, weighted by the lines of code (LOC) changed.

### Network Construction Process

The scripts construct directed networks where:
- Nodes represent individual developers or companies
- Edges connect developers who modified the same file(s) during a release cycle
- Edge weights correspond to the LOC changed by each developer
- Node attributes include developer identifiers and affiliations

For example, if developer A modifies 5 LOC in file F and developer B modifies 6 LOC in file F during the same release, the script creates two directed edges:
- A → B with weight 5
- B → A with weight 6

### Data Processing Pipeline

#### Repository Setup
- Automatically clones the target repository if not already present
- Fetches all repository releases (using either GitHub releases or tags)
- Analyses commits using the local git repository
- Falls back to GitHub API for commits not found locally

#### User Identity Processing
- Loads pre-processed merged user data
- Assigns unique identifiers (UIDs) to authors through a hierarchical matching process:
  1. Matches both author name AND email against merged users data
  2. Falls back to matching either author name OR email
  3. Assigns UID -1 if no match is found

#### Data Aggregation
- Aggregates commit data between unique releases
- Tallies LOC metrics (added, deleted, changed) for multiple commits to the same file by the same user
- Filters out bot commits during data collection

### Input Requirements
- GitHub repository URL
- Merged users data file
- GitHub API credentials
- Release/tag information

### Output
- Edge lists representing developer collaboration networks
- Commit data cache for verification and reanalysis

## Contact
For enquiries or feedback, please contact cailean.osborne@oii.ox.ac.uk
