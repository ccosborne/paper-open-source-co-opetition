# Commit Network Analysis Scripts

## Overview

This repository contains Python scripts that generate directed network edge lists representing developer collaboration patterns based on shared file modifications between software releases. The scripts analyse commit patterns and construct networks where edges represent shared file touches between developers, weighted by the lines of code (LOC) changed.

## Network Construction Process

The scripts construct directed networks where:
- Nodes represent individual developers or companies
- Edges connect developers who modified the same file(s) during a release cycle
- Edge weights correspond to the LOC changed by each developer
- Node attributes include developer identifiers and affiliations

For example, if developer A modifies 5 LOC in file F and developer B modifies 6 LOC in file F during the same release, the script creates two directed edges:
- A → B with weight 5
- B → A with weight 6

## Data Processing Pipeline

### Repository Setup
- Automatically clones the target repository if not already present
- Fetches all repository releases (using either GitHub releases or tags)
- Analyses commits using the local git repository
- Falls back to GitHub API for commits not found locally

### User Identity Processing
- Loads pre-processed merged user data
- Assigns unique identifiers (UIDs) to authors through a hierarchical matching process:
  1. Matches both author name AND email against merged users data
  2. Falls back to matching either author name OR email
  3. Assigns UID -1 if no match is found

### Data Aggregation
- Aggregates commit data between unique releases
- Tallies LOC metrics (added, deleted, changed) for multiple commits to the same file by the same user
- Filters out bot commits during data collection

## Input Requirements
- GitHub repository URL
- Merged users data file
- GitHub API credentials
- Release/tag information

## Output
- Edge lists representing developer collaboration networks
- Commit data cache for verification and reanalysis