import pandas as pd
import os

input_file = '../data/top_1000_github_repos_with_commits_v2.csv'
df = pd.read_csv(input_file)

# Five lines were randomly selected as the scoring set.
scoring_df = df.sample(n=5, random_state=42)

# The remaining 995 lines are used as the training set.
train_df = df.drop(scoring_df.index)

train_df.to_csv('../data/model_train_data.csv', index=False)
scoring_df.to_csv('../data/model_scoring_data.csv', index=False)

print(f" Data partitioning completed")
print(f" Training set (model_train_data.csv): {len(train_df)} rows")
print(f" Scoring set (model_scoring_data.csv): {len(scoring_df)} rows")