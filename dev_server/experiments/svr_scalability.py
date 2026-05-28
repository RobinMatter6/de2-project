import pandas as pd
import numpy as np
import time
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR
from sklearn.model_selection import GridSearchCV, KFold

import ray
import joblib
from ray.util.joblib import register_ray

print("Connecting to Ray cluster for SVR SCALABILITY TEST...")
ray.init(address='auto')

# Loading and inflating the dataset
df = pd.read_csv('../../data/raw/top_1000_github_repos_with_commits_v2.csv')

# Expanding to 20,000 rows for scalability test
df = pd.concat([df] * 20, ignore_index=True)
print(f"Inflated dataset size for SVR: {len(df)} rows")

bool_columns = ['has_wiki', 'has_pages', 'has_discussions', 'archived']
df[bool_columns] = df[bool_columns].astype(int)

TOP_N = 5
top_languages = df['language'].value_counts().nlargest(TOP_N).index.tolist()
df['language'] = df['language'].fillna('Other')
df['language'] = df['language'].apply(lambda x: x if x in top_languages else 'Other')
df_encoded = pd.get_dummies(df, columns=['language'], drop_first=False)

X = df_encoded.drop(['repo_name', 'stars'], axis=1)
y_log = np.log1p(df_encoded['stars'])

pipeline = Pipeline([('scaler', StandardScaler()), ('model', SVR())])

# Smaller, more numerous tasks prevent a single core from getting stuck with all heavy workloads.
param_grid = {
    'model__C': [0.1, 1.0, 5.0, 10.0], 
    'model__kernel': ['linear', 'rbf'],
    'model__gamma': ['scale', 'auto']
}

cv_strategy = KFold(n_splits=3, shuffle=True, random_state=42)

# Define different compute scales
machine_configs = {
    "1 Machine (2 Cores)": 2,
    "2 Machines (4 Cores)": 4,
    "3 Machines (6 Cores)": 6
}

print("\n" + "="*50)
print("STARTING SVR SCALABILITY TEST (20,000 Rows)")
print("="*50)

register_ray()

results = {}

for label, cores in machine_configs.items():
    print(f"\n--- Testing configuration: {label} ---")
    
    # Dynamically limit the number of concurrent tasks to simulate machine count
    # This prevents Joblib from batching and assigning too many tasks to a worker upfront,
    # forcing a dynamic, First-Come-First-Serve load balancing strategy.
    grid = GridSearchCV(
        estimator=pipeline,
        param_grid=param_grid,
        cv=cv_strategy,
        scoring='r2',
        n_jobs=cores,
        pre_dispatch='1*n_jobs'
    )
    
    start_time = time.time()
    
    with joblib.parallel_backend('ray'):
        grid.fit(X, y_log)
        
    execution_time = time.time() - start_time
    results[label] = execution_time
    print(f"Time taken: {execution_time:.2f} seconds")

print("\n" + "="*50)
print("FINAL SVR SCALABILITY RESULTS:")
for label, t in results.items():
    print(f"{label}: {t:.2f} seconds")
print("="*50)