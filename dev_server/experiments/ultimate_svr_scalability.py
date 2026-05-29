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

print("Connecting to Ray cluster for ULTIMATE SVR SCALABILITY TEST...")
ray.init(address='auto')

# Loading and inflating the dataset to 20,000 rows
df = pd.read_csv('../../data/raw/top_1000_github_repos_with_commits_v2.csv')
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

# Pruned Grid Size (Removed extreme C=50, 100 to prevent mathematical non-convergence)
param_grid = {
    'model__C': [0.1, 1.0, 10.0], 
    'model__kernel': ['linear', 'rbf'], 
    'model__gamma': ['scale', 'auto'] 
}

# 3-fold CV to save time
cv_strategy = KFold(n_splits=3, shuffle=True, random_state=42)

machine_configs = {
    "1 Machine (2 Cores)": 2,
    "2 Machines (4 Cores)": 4,
    "3 Machines (6 Cores)": 6
}

print("\n" + "="*50)
print("STARTING ULTIMATE SVR SCALABILITY TEST (20k Rows, 3 Folds, Pruned Grid)")
print("="*50)

register_ray()

results = {}

for label, cores in machine_configs.items():
    print(f"\n--- Testing configuration: {label} ---")
    
    grid = GridSearchCV(
        estimator=pipeline,
        param_grid=param_grid,
        cv=cv_strategy,
        scoring='r2',
        n_jobs=cores,
    )
    
    start_time = time.time()
    
    with joblib.parallel_backend('ray'):
        grid.fit(X, y_log)
        
    execution_time = time.time() - start_time
    results[label] = execution_time
    print(f"Time taken: {execution_time:.2f} seconds")

print("\n" + "="*50)
print("FINAL ULTIMATE SVR SCALABILITY RESULTS:")
for label, t in results.items():
    print(f"{label}: {t:.2f} seconds")
print("="*50)