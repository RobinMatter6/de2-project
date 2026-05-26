# %%
import os
import requests
import time
import pandas as pd
import re
import getpass

# %%
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

if not GITHUB_TOKEN:
    print("No system environment variables detected GITHUB_TOKEN。")
    GITHUB_TOKEN = getpass.getpass("Please paste your GitHub Token here and press Enter: ")

HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

print("Token configured and request headers are ready")

# %%
def get_top_repositories(min_stars=50, total_needed=1000):
    repos = []
    page = 1
    per_page = 100
    
    print(f"Starting to fetch GitHub repositories with stars >= {min_stars}...")
    
    while len(repos) < total_needed:
        # using GitHub Search API
        search_url = f"https://api.github.com/search/repositories?q=stars:>={min_stars}&sort=stars&order=desc&per_page={per_page}&page={page}"
        
        response = requests.get(search_url, headers=HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            
            if not items:
                print("No more data available.")
                break
                
            repos.extend(items)
            print(f"Page {page} fetched successfully, total so far: {len(repos)} repositories.")
            page += 1
            time.sleep(1) # Rate‑limit–compliant anti‑ban throttling
        else:
            print(f" Request error: {response.status_code}")
            print(response.json())
            break
            
    return repos[:total_needed]

# %%
top_repos_raw = get_top_repositories()

# Extract the required basic fields and convert to DataFrame
if top_repos_raw:
    repo_data_list = [{
        'repo_name': repo['full_name'],
        'stars': repo['stargazers_count'],
        'forks': repo['forks_count'],       
        'watchers': repo['watchers_count'], 
        'language': repo['language'],
        'url': repo['url']
    } for repo in top_repos_raw]
    
    df_repos = pd.DataFrame(repo_data_list)
    
    df_repos.to_csv('../../data/raw/top_1000_github_repos.csv', index=False)
    print("\n Data successfully saved to top_1000_github_repos.csv")

# %%
import re

def get_total_commits(repo_full_name):
    """Get the total number of commits via the Link header to avoid iterating through all pages"""
    commits_url = f"https://api.github.com/repos/{repo_full_name}/commits?per_page=1"
    try:
        response = requests.get(commits_url, headers=HEADERS)
        
        if response.status_code == 200:
            if 'Link' in response.headers:
                link_header = response.headers['Link']
                last_page_match = re.search(r'page=(\d+)>; rel="last"', link_header)
                if last_page_match:
                    return int(last_page_match.group(1))
            # If there is no Link header, it means there is only 1 commit or the dataset is very small
            return len(response.json())
        elif response.status_code == 409:
            return 0 # 409 response usually indicates an empty repository
        elif response.status_code == 403:
            print(f"\n Rate limit triggered. Pausing for 60 seconds before retrying...")
            time.sleep(60)
            return get_total_commits(repo_full_name) # Recursive retry
        else:
            print(f"Failed to fetch commits for {repo_full_name}: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"Request exception: {e}")
        return None

# Prepare a list to store the retrieved commits
commits_list = []
total_repos = len(df_repos)

print(f" Starting to fetch Commits data for these {total_repos} repositories (1000 requests needed, please wait)...")

for index, row in df_repos.iterrows():
    repo_name = row['repo_name']
    commits = get_total_commits(repo_name)
    commits_list.append(commits)
    
    # Log progress every 50 items to indicate the script is still active.
    if (index + 1) % 50 == 0:
        print(f" Processed {index + 1}/{total_repos} repositories...")
        
    time.sleep(0.2)

# Add the new features to the existing DataFrame
df_repos['commits'] = commits_list

# Save as the final CSV containing the commits.
df_repos.to_csv('../../data/raw/top_1000_github_repos_with_commits.csv', index=False)

print("\n Feature extraction completed successfully. Data saved to top_1000_github_repos_with_commits.csv")



