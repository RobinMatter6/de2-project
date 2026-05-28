import numpy as np
import pandas as pd
import time
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV, KFold

import ray
import joblib
from ray.util.joblib import register_ray

print("Connecting to Ray cluster for STRESS TEST...")
ray.init(address='auto')

# Loading the original dataset
df = pd.read_csv('../../data/raw/top_1000_github_repos_with_commits_v2.csv')

# Copy 100 times, become 100,000 rows
print(f"Original dataset size: {len(df)} rows")
df = pd.concat([df] * 100, ignore_index=True)
print(f"Inflated dataset size for STRESS TEST: {len(df)} rows")

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
    ('model', RandomForestRegressor(random_state=42))
])

param_grid = {
    'model__n_estimators': [100, 200], 
    'model__max_depth': [10, 20]      
}

cv_strategy = KFold(n_splits=3, shuffle=True, random_state=42)

grid = GridSearchCV(
    estimator=pipeline,
    param_grid=param_grid,
    cv=cv_strategy,
    scoring='r2',
    n_jobs=-1
)

print("\n--- INITIATING 100K ROWS STRESS TEST ---")
start_time = time.time()

register_ray()
with joblib.parallel_backend('ray'):
    grid.fit(X, y_log)

end_time = time.time()
execution_time = end_time - start_time

print(f"\nStress Test Total Distributed Training Time: {execution_time:.2f} seconds")