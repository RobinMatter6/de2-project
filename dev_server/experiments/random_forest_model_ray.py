import numpy as np
import pandas as pd
import time
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV, KFold

# Introducing Ray and Joblib
import ray
import joblib
from ray.util.joblib import register_ray

# Connecting to Ray cluster
print("Connecting to Ray cluster...")
ray.init(address='auto')

# Load data
df = pd.read_csv('../../data/raw/top_1000_github_repos_with_commits_v2.csv')

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

# Increasing parameter grid
param_grid = {
    'model__n_estimators': [100, 200, 300, 500], # the number of trees in the forest
    'model__max_depth': [10, 20, 30, None],      # deeper trees can capture more complex patterns but may overfit
    'model__min_samples_split': [2, 5, 10]       # more detailed node splitting
}

cv_strategy = KFold(n_splits=5, shuffle=True, random_state=42)

grid = GridSearchCV(
    estimator=pipeline,
    param_grid=param_grid,
    cv=cv_strategy,
    scoring='r2',
    n_jobs=-1
)

print("\n--- Random Forest Distributed Tuning via Ray ---")
print("Starting intensive hyperparameter search across the cluster...")

start_time = time.time()

# Register Ray as the backend for Joblib to enable distributed execution
import joblib
from ray.util.joblib import register_ray
register_ray()

with joblib.parallel_backend('ray'):
    grid.fit(X, y_log)

end_time = time.time()
execution_time = end_time - start_time

print(f"\nBest Parameters: {grid.best_params_}")
print(f"Best CV R-squared: {grid.best_score_:.4f}")
print(f"Total Distributed Training Time: {execution_time:.2f} seconds")