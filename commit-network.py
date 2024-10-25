import csv
import os
import requests
from datetime import datetime, timedelta
import requests
import config
from common import get_with_timeout, handle_rate_limit
import git
from git import RemoteProgress
from tqdm.auto import tqdm
import bot_dict
import json

class CloneProgress(RemoteProgress):
    def __init__(self):
        super().__init__()
        self.pbar = tqdm(position=0, leave=True, dynamic_ncols=True)
        self.pbar.total = 100
        self.pbar.n = 0
        self.pbar.refresh()

    def update(self, op_code, cur_count, max_count=None, message=''):
        self.pbar.total = max_count
        self.pbar.n = cur_count
        self.pbar.refresh()

merged_user_id = {}

def get_commit_stats_api(repo_owner, repo_name, sha):
    headers = {
        'Authorization': f'token {config.github_token}',
        'User-Agent': 'request',
        'Accept': 'application/vnd.github.v3+json'
    }

    # Set the initial variables
    page = 1
    page_count = 1
    file_stats = []

    while True:
        try:
            # Send a GET request to the commit data API endpoint
            response = get_with_timeout(
                f'https://api.github.com/repos/{repo_owner}/{repo_name}/commits/{sha}',
                headers=headers,
                params={'per_page': 100, 'page': page}
            )

            if response is None:
                print(f"An error occurred while fetching commit data for https://api.github.com/repos/{repo_owner}/{repo_name}/commits/{sha}")
                break
            
            commit_data = response.json()
            
            # Check if there are more commits to retrieve
            if page == 1 and 'Link' in response.headers:
                links = response.headers['Link'].split(', ')
                page_count = int(next(link for link in links if 'rel="last"' in link).split('&page=')[1].split('>;')[0])

            # Iterate over the commits and get stats
            #file_list_len = len(commit_data['files'])
            for i, file in enumerate(commit_data['files']):
                file_name = file['filename']
                additions = file['additions']
                deletions = file['deletions']
                changes = file['changes']
                file_stats.append((file_name, additions, deletions, changes))
                
            #print(f'{repo_name}: Getting commit data... ({page}/{page_count})')

            # Check if there are more commits to retrieve
            if 'Link' in response.headers:
                links = response.headers['Link'].split(', ')
                try:
                    next_link = next(link for link in links if 'rel="next"' in link)
                    if next_link:
                        page += 1
                    else:
                        break
                except StopIteration:
                    break
            else:
                break
        except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as e:
            print(f"An error occurred while fetching commit data for https://api.github.com/repos/{repo_owner}/{repo_name}/commits/{sha}: {str(e)}")
            break

    return file_stats

def get_commit_stats(sha):
    file_stats = []
    try:
        files = cur_repo.git.execute(['git', 'show' '', '--numstat', '--format=', f'{sha}'])
        commit_lines = str(files).splitlines()
        for i, line in enumerate(commit_lines):
            line_segments = line.split('\t')
            additions = int(line_segments[0])
            deletions = int(line_segments[1])
            file_name = line_segments[2]
            file_stats.append((file_name, additions, deletions, additions + deletions))
    except:
        #print(f'{repo_name}: Failed to locally retrieve commit stats for {sha}')
        return None
    return file_stats

def get_release_dates(repo_owner, repo_name):
    headers = {
        'Authorization': f'token {config.github_token}',
        'User-Agent': 'request',
        'Accept': 'application/vnd.github.v3+json'
    }

    releases_dates = {}
    page = 1

    while True:
        try:
            # Send a GET request to the releases API endpoint
            response = get_with_timeout(
                f'https://api.github.com/repos/{repo_owner}/{repo_name}/releases',
                headers=headers,
                params={'per_page': 100, 'page': page}
            )

            # Check if the response was successful
            if response and response.status_code == 200:
                releases_data = response.json()

                for release in releases_data:
                    release_date = datetime.strptime(release['published_at'], "%Y-%m-%dT%H:%M:%SZ")
                    release_tag = release['tag_name']

                    rel_date = releases_dates.get(release_tag, None)
                    if (rel_date != None):
                        print(f"{release_tag} already exists!")

                    releases_dates[release_tag] = release_date

            # Check if there are more commits to retrieve
            if 'Link' in response.headers:
                links = response.headers['Link'].split(', ')
                try:
                    next_link = next(link for link in links if 'rel="next"' in link)
                    if next_link:
                        page += 1
                    else:
                        break
                except StopIteration:
                    break
            else:
                break
        except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as e:
            print(f"An error occurred while fetching commit data for https://api.github.com/repos/{repo_owner}/{repo_name}/releases?per_page{100}&page={page}: {str(e)}")
            break

    if (repo_get_tags is True):
        page = 1
        while True:
            try:
                # Send a GET request to the tags API endpoint
                response = get_with_timeout(
                    f'https://api.github.com/repos/{repo_owner}/{repo_name}/tags',
                    headers=headers,
                    params={'per_page': 100, 'page': page}
                )

                if response and response.status_code == 200:
                    tags = response.json()

                    for tag in tags:
                        tag_name = tag['name']
                        tag_commit_sha = tag['commit']['sha']

                        rel_date = releases_dates.get(tag_name, None)
                        if (rel_date != None):
                            continue

                        commit_response = get_with_timeout(
                            f'https://api.github.com/repos/{repo_owner}/{repo_name}/commits/{tag_commit_sha}',
                            headers=headers
                        )

                        if commit_response and commit_response.status_code == 200:
                            commit_data = commit_response.json()
                            commit_date_str = commit_data['commit']['committer']['date']
                            commit_date = datetime.strptime(commit_date_str, '%Y-%m-%dT%H:%M:%SZ')
                            releases_dates[tag_name] = commit_date

                # Check if there are more commits to retrieve
                if 'Link' in response.headers:
                    links = response.headers['Link'].split(', ')
                    try:
                        next_link = next(link for link in links if 'rel="next"' in link)
                        if next_link:
                            page += 1
                        else:
                            break
                    except StopIteration:
                        break
                else:
                    break
            except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as e:
                print(f"An error occurred while fetching commit data for https://api.github.com/repos/{repo_owner}/{repo_name}/commits?per_page{100}&page={page}: {str(e)}")
                break
    
    return releases_dates

def get_merged_user_id(commit_author, merged_user_data):
    user_id = merged_user_id.get((commit_author.name, commit_author.email), None)
    if (user_id != None):
        return user_id
    
    # Check to see if the email and name is contained.
    for key in merged_user_data:
        emails = merged_user_data[key]['emails']
        names = merged_user_data[key]['names']

        if (commit_author.name in names and commit_author.email in emails):
            merged_user_id[(commit_author.name, commit_author.email)] = key
            return key

    # Fall back to name or email lookup
    for key in merged_user_data:
        emails = merged_user_data[key]['emails']
        names = merged_user_data[key]['names']

        if (commit_author.name in names or commit_author.email in emails):
            merged_user_id[(commit_author.name, commit_author.email)] = key
            return key

    return -1

def get_commit_list(repo, cutoff_date, release_dates, merged_user_data):
    repo_commits = list(repo.iter_commits())
    pbar = tqdm(total=len(repo_commits), position=0, leave=True, dynamic_ncols=True)
    commit_list_network = {}

    for i, commit in enumerate(repo_commits):
        pbar.n = i
        pbar.refresh()

        # If the commit was made after the cutoff date then skip it.
        if datetime.fromtimestamp(commit.authored_date) > cutoff_date:
            continue

        commit_sha = git.to_hex_sha(commit.binsha).decode("utf-8")

        # Try get commit data from local repository
        commit_data = get_commit_stats(commit_sha)

        # Fall back to GitHub API if it fails
        if commit_data is None:
            commit_data = get_commit_stats_api(repo_owner, repo_name, commit_sha) #(file_name, additions, deletions, changes))
        
        # Skip this commit if it was made by a bot
        bot_info = bot_dict.bot_dict[f'{repo_owner}/{repo_name}']
        if commit.author.name in bot_info or commit.author.email in bot_info:
            continue

        merged_user_id = get_merged_user_id(commit.author, merged_user_data)
        closest_release = get_closest_release(release_dates, commit)

        for file in commit_data:
            file_name = file[0]
            file_additions = int(file[1])
            file_deletions = int(file[2])
            file_changes = int(file[3])
            edge_key = (merged_user_id, file_name, closest_release)
            edge_value = commit_list_network.get(edge_key, None)
            if edge_value is not None:
                file_additions += int(edge_value[2])
                file_deletions += int(edge_value[3])
                file_changes += int(edge_value[4])
            commit_list_network[edge_key] = (commit.author.name, commit.author.email, file_additions, file_deletions, file_changes)

    pbar.close()
    tqdm._instances.clear()
    return commit_list_network

def get_closest_release(release_dates, commit):
    commit_timestamp = datetime.fromtimestamp(commit.authored_date)
    closest_release = None
    min_difference = timedelta.max

    for release_tag, release_date in release_dates.items():
        difference = release_date - commit_timestamp
        if difference > timedelta() and difference < min_difference:
            min_difference = difference
            closest_release = release_tag

    return closest_release

def sort_cln_by_file(commit_list_network):
    sorted_cln = {}

    for i, commit in enumerate(commit_list_network):
        uid = commit[0]
        file = commit[1]
        release = commit[2]
        source_aname = commit_list_network[commit][0]
        source_aemail = commit_list_network[commit][1]
        loc_added = int(commit_list_network[commit][2])
        loc_deleted = int(commit_list_network[commit][3])
        loc_changed = int(commit_list_network[commit][4])
        
        sorted_cln_file = sorted_cln.get(file, None)
        if (sorted_cln_file is None):
            sorted_cln[file] = [(uid, release, source_aname, source_aemail, loc_added, loc_deleted, loc_changed)]
        else:
            sorted_cln_file.append((uid, release, source_aname, source_aemail, loc_added, loc_deleted, loc_changed))
            sorted_cln[file] = sorted_cln_file

    return sorted_cln

def write_longitudinal_network_cln_to_file(final_cln):
    # CSV file
    commit_data_file = f"{repo_name}_longitudinal_commit_network.csv"
    commit_data_path = os.path.join(data_folder, commit_data_file)

    fields = ['source-uid', 'source-name', 'source-email', 'target-uid', 'target-name', 'target-email', 'release', 'release-date', 'loc-added', 'loc-deleted', 'loc-changed']
    
    # If the file doesn't exist, create a new file
    if not os.path.exists(commit_data_path):
        with open(commit_data_path, 'w') as file:
            writer = csv.writer(file)
            writer.writerow(fields)

    # Write to csv file
    print(f'{repo_name}: Saving longitudinal commit list network edge to file...')
    pbar = tqdm(total=len(final_cln), position=0, leave=True, dynamic_ncols=True)
    pbar.n = 0
    with open(commit_data_path, 'a') as file:
        writer = csv.writer(file)
        for i, cln_key in enumerate(final_cln):
            pbar.n = i + 1
            pbar.refresh()
            source_uid = cln_key[0]
            target_uid = cln_key[1]
            source_release = cln_key[2]
            
            source_aname = final_cln[cln_key][0]
            source_aemail = final_cln[cln_key][1]
            target_aname = final_cln[cln_key][2]
            target_aemail = final_cln[cln_key][3]
            loc_added = int(final_cln[cln_key][4])
            loc_deleted = int(final_cln[cln_key][5])
            loc_changed = int(final_cln[cln_key][6])
            writer.writerow((source_uid, source_aname, source_aemail, target_uid, target_aname, target_aemail, source_release, releases_dates[source_release], loc_added, loc_deleted, loc_changed))
    pbar.close()
    tqdm._instances.clear()

def create_bipartite_network_cln(repo_name, data_folder, final_cln, write_bipartite_cln_to_file):
    # CSV file
    commit_data_file = f"{repo_name}_commit_network.csv"
    commit_data_path = os.path.join(data_folder, commit_data_file)

    flattened_cln = {}

    # Write to csv file
    if write_bipartite_cln_to_file:
        print(f'{repo_name}: Saving commit list network edge to file...')

        fields = ['source-uid', 'source-name', 'source-email', 'target-uid', 'target-name', 'target-email', 'filepath', 'release', 'release-date', 'loc-added', 'loc-deleted', 'loc-changed']
    
        # If the file doesn't exist, create a new file
        if not os.path.exists(commit_data_path):
            with open(commit_data_path, 'w') as file:
                writer = csv.writer(file)
                writer.writerow(fields)
    else:
        print(f'{repo_name}: Generating commit list network edge to file...')

    pbar = tqdm(total=len(final_cln), position=0, leave=True, dynamic_ncols=True)
    pbar.n = 0
    with open(commit_data_path, 'a') as file:
        if write_bipartite_cln_to_file:
            writer = csv.writer(file)
        for i, cln_file in enumerate(final_cln):
            pbar.n = i + 1
            pbar.refresh()
            for source_point in final_cln[cln_file]:
                source_uid = source_point[0]
                source_release = source_point[1]
                source_aname = source_point[2]
                source_aemail = source_point[3]
                for target_point in final_cln[cln_file]:
                    target_uid = target_point[0]
                    target_release = target_point[1]
                    if (source_release == target_release) and (source_uid != target_uid):
                        target_aname = target_point[2]
                        target_aemail = target_point[3]
                        loc_added = int(source_point[4])
                        loc_deleted = int(source_point[5])
                        loc_changed = int(source_point[6])

                        if write_bipartite_cln_to_file:
                            writer.writerow((source_uid, source_aname, source_aemail, target_uid, target_aname, target_aemail, cln_file, source_release, releases_dates[source_release], loc_added, loc_deleted, loc_changed))
                        
                        flattened_cln_key = (source_uid, target_uid, source_release)
                        flattened_cln_value = flattened_cln.get(flattened_cln_key, None)
                        if (flattened_cln_value is None):
                            flattened_cln[flattened_cln_key] = (source_aname, source_aemail, target_aname, target_aemail, loc_added, loc_deleted, loc_changed)
                        else:
                            flattened_cln[flattened_cln_key] = (source_aname, source_aemail, target_aname, target_aemail, 
                                                                int(flattened_cln_value[4]) + loc_added, 
                                                                int(flattened_cln_value[5]) + loc_deleted, 
                                                                int(flattened_cln_value[6]) + loc_changed)
    
    # Cleanup left over file
    if write_bipartite_cln_to_file is False:
        os.remove(commit_data_path)

    pbar.close()
    tqdm._instances.clear()
    return flattened_cln

def create_static_cln(final_cln):
    # CSV file
    commit_data_file = f"{repo_name}_static_commit_network.csv"
    commit_data_path = os.path.join(data_folder, commit_data_file)

    final_static_cln = {}
    for i, cln_key in enumerate(final_cln):
        source_uid = cln_key[0]
        target_uid = cln_key[1]
        source_aname = final_cln[cln_key][0]
        source_aemail = final_cln[cln_key][1]
        target_aname = final_cln[cln_key][2]
        target_aemail = final_cln[cln_key][3]
        loc_added = int(final_cln[cln_key][4])
        loc_deleted = int(final_cln[cln_key][5])
        loc_changed = int(final_cln[cln_key][6])
        
        static_cln_key = (source_uid, target_uid)
        static_cln_value = final_static_cln.get(static_cln_key, None)
        if (static_cln_value is None):
            final_static_cln[static_cln_key] = (source_aname, source_aemail, target_aname, target_aemail, loc_added, loc_deleted, loc_changed)
        else:
            final_static_cln[static_cln_key] = (source_aname, source_aemail, target_aname, target_aemail, 
                                                int(static_cln_value[4]) + loc_added, 
                                                int(static_cln_value[5]) + loc_deleted, 
                                                int(static_cln_value[6]) + loc_changed)

    fields = ['source-uid', 'source-name', 'source-email', 'target-uid', 'target-name', 'target-email', 'loc-added', 'loc-deleted', 'loc-changed']
    
    # If the file doesn't exist, create a new file
    if not os.path.exists(commit_data_path):
        with open(commit_data_path, 'w') as file:
            writer = csv.writer(file)
            writer.writerow(fields)

    # Write to csv file
    print(f'{repo_name}: Saving static commit list network edge to file...')
    pbar = tqdm(total=len(final_static_cln), position=0, leave=True, dynamic_ncols=True)
    pbar.n = 0
    with open(commit_data_path, 'a') as file:
        writer = csv.writer(file)
        for i, cln_key in enumerate(final_static_cln):
            pbar.n = i + 1
            pbar.refresh()
            source_uid = cln_key[0]
            target_uid = cln_key[1]
            
            source_aname = final_static_cln[cln_key][0]
            source_aemail = final_static_cln[cln_key][1]
            target_aname = final_static_cln[cln_key][2]
            target_aemail = final_static_cln[cln_key][3]
            loc_added = int(final_static_cln[cln_key][4])
            loc_deleted = int(final_static_cln[cln_key][5])
            loc_changed = int(final_static_cln[cln_key][6])
            writer.writerow((source_uid, source_aname, source_aemail, target_uid, target_aname, target_aemail, loc_added, loc_deleted, loc_changed))
    pbar.close()
    tqdm._instances.clear()

# Create the 'Data' folder if it doesn't exist
data_folder = 'Data/Network'
repo_folder = 'Data/Repo'
merged_users_folder = 'Data/Merged_Users'
commit_list_folder = cur_repo_folder = os.path.join(data_folder, 'Commits')

os.makedirs(data_folder, exist_ok=True)

# Iterate over the repositories and collect commit data
for repo in config.repo_list:
    # Specify parameters
    repo_name = repo['name']
    repo_owner = repo['owner']
    repo_get_tags = repo['get_tags']
    cutoff_date = datetime(2022, 9, 12)

    cur_repo_folder = os.path.join(repo_folder, repo_name)
    print(f'{repo_name}: Looking for repository...')
    if not os.path.exists(cur_repo_folder):
        print(f'{repo_name}: Failed to find repository, cloning repository...')
        git.Repo.clone_from(f'https://github.com/{repo_owner}/{repo_name}.git', cur_repo_folder, progress=CloneProgress())
        tqdm._instances.clear()

    cur_repo = git.Repo(cur_repo_folder)
    print(f'{repo_name}: Finished setting up local repository')

    # Get the release dates for the repository
    print(f'{repo_name}: Fetching releases...')
    releases_dates = get_release_dates(repo_owner, repo_name)
    print(f'{repo_name}: {len(releases_dates)} releases')

    # Load the merged user data
    with open(f'{merged_users_folder}/{repo_name}.json', 'r') as json_file:
        merged_user_data = json.load(json_file)

    # Get the commit list for the repository
    os.makedirs(commit_list_folder, exist_ok=True)
    print(f'{repo_name}: Looking for saved commits...')
    commit_list_file_path = os.path.join(commit_list_folder, f'{repo_name}_commit_list.csv')
    commit_list_network = {}
    if not os.path.exists(commit_list_file_path):
        print(f'{repo_name}: Failed to find saved commits, retrieving commits...')
        commit_list_network = get_commit_list(cur_repo, cutoff_date, releases_dates, merged_user_data)

        print(f'{repo_name}: Savings commits...')
        with open(commit_list_file_path, 'w') as csv_file:
            writer = csv.writer(csv_file)
            for i, commit in enumerate(commit_list_network):
                writer.writerow((commit[0], commit[1], commit[2], releases_dates[commit[2]],
                                commit_list_network[commit][0], 
                                commit_list_network[commit][1], 
                                commit_list_network[commit][2], 
                                commit_list_network[commit][3], 
                                commit_list_network[commit][4]))
    else:
        print(f'{repo_name}: Loading saved commits...')
        with open(commit_list_file_path, 'r') as csv_file:
            reader = csv.reader(csv_file)
            for row in reader:
                edge_key = (row[0], row[1], row[2])
                commit_list_network[edge_key] = (row[4], row[5], row[6], row[7], row[8])

    # Sort the CLN by file path to improve network edge list creation efficiency
    print(f'{repo_name}: Sorting commits by file...')
    sorted_cln = sort_cln_by_file(commit_list_network)
    
    # Make the bipartite cln
    write_bipartite_cln_to_file = False
    longitudinal_cln = create_bipartite_network_cln(repo_name, data_folder, sorted_cln, write_bipartite_cln_to_file)

    # Write to file
    write_longitudinal_network_cln_to_file(longitudinal_cln)

    # Create and write static cln
    create_static_cln(longitudinal_cln)

    print(f'{repo_name}: Done!')