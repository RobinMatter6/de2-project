import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.compose import TransformedTargetRegressor
from sklearn.svm import SVR
from sklearn.model_selection import GridSearchCV, KFold

# Load Data
df = pd.read_csv('../data/top_1000_github_repos_with_commits.csv')

# Handle the 'language' feature
TOP_N = 5
top_languages = df['language'].value_counts().nlargest(TOP_N).index.tolist()
df['language'] = df['language'].fillna('Other')
df['language'] = df['language'].apply(lambda x: x if x in top_languages else 'Other')
df_encoded = pd.get_dummies(df, columns=['language'], drop_first=False)

# Split dataset into features and target, use log scale for y for power law
X = df_encoded.drop(['repo_name', 'url', 'stars', 'watchers'], axis=1)
y_log = np.log1p(df_encoded['stars'])

# Build the nested Pipeline
pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('model', SVR())
])

# Setup GridSearch Hyperparameters
param_grid = {
    'model__C': [0.1, 1.0, 10.0],
    'model__kernel': ['linear', 'rbf']
}

# Make sure to shuffle data for cv
cv_strategy = KFold(n_splits=5, shuffle=True, random_state=42)


# Train and Evaluate
grid = GridSearchCV(
    estimator=pipeline,
    param_grid=param_grid,
    cv=cv_strategy,
    scoring='r2',
    n_jobs=-1
)

print("--- Support Vector Regression (SVR) Tuning ---")
print("Training models... (This may take a few minutes)")
grid.fit(X, y_log)

print(f"Best Parameters: {grid.best_params_}")
print(f"Best CV R-squared: {grid.best_score_:.4f}")
