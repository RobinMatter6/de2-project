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

print("Connecting to Ray cluster for SVR STRESS TEST...")
ray.init(address='auto')

# Loading and inflating the dataset
df = pd.read_csv('../../data/raw/top_1000_github_repos_with_commits_v2.csv')
print(f"Original dataset size: {len(df)} rows")

# Copy 10 times, become 10,000 rows
df = pd.concat([df] * 10, ignore_index=True)
print(f"Inflated dataset size for SVR STRESS TEST: {len(df)} rows")

bool_columns = ['has_wiki', 'has_pages', 'has_discussions', 'archived']
df[bool_columns] = df[bool_columns].astype(int)

TOP_N = 5
top_languages = df['language'].value_counts().nlargest(TOP_N).index.tolist()
df['language'] = df['language'].fillna('Other')
df['language'] = df['language'].apply(lambda x: x if x in top_languages else 'Other')
df_encoded = pd.get_dummies(df, columns=['language'], drop_first=False)

X = df_encoded.drop(['repo_name', 'stars'], axis=1)
y_log = np.log1p(df_encoded['stars'])

pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('model', SVR())
])

# Moderately increased grid size for stress testing
param_grid = {
    'model__C': [0.1, 1.0, 10.0], 
    'model__kernel': ['linear', 'rbf'] 
}

cv_strategy = KFold(n_splits=3, shuffle=True, random_state=42)

grid = GridSearchCV(
    estimator=pipeline,
    param_grid=param_grid,
    cv=cv_strategy,
    scoring='r2',
    n_jobs=-1
)

print("\n--- INITIATING 10,000 ROWS SVR STRESS TEST ---")
start_time = time.time()

register_ray()
with joblib.parallel_backend('ray'):
    grid.fit(X, y_log)

end_time = time.time()
execution_time = end_time - start_time

print(f"\nSVR Stress Test Total Distributed Training Time: {execution_time:.2f} seconds")