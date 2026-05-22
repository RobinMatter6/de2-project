import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV, KFold

# Load data
df = pd.read_csv('../data/top_1000_github_repos_with_commits_v2.csv')

# Convert boolean features into numerical
bool_columns = ['has_wiki', 'has_pages', 'has_discussions', 'archived']
df[bool_columns] = df[bool_columns].astype(int)

# 2. Handle the 'language' feature
TOP_N = 5
top_languages = df['language'].value_counts().nlargest(TOP_N).index.tolist()
df['language'] = df['language'].fillna('Other')
df['language'] = df['language'].apply(lambda x: x if x in top_languages else 'Other')
df_encoded = pd.get_dummies(df, columns=['language'], drop_first=False)

# Split data into features and target
X = df_encoded.drop(['repo_name', 'stars'], axis=1)
y_log = np.log1p(df_encoded['stars'])

# Create pipeline
pipeline = Pipeline([
	('scaler', StandardScaler()),
	('model', RandomForestRegressor(random_state=42))
])


# GridSearch parameters
param_grid = {
	'model__n_estimators':[100, 200],
	'model__max_depth': [10, 20, None]
}

# Shuffle the data for the cross-validation
cv_strategy = KFold(n_splits=5, shuffle=True, random_state=42)

# Train and evaluate
grid = GridSearchCV(
	estimator=pipeline,
	param_grid=param_grid,
	cv=cv_strategy,
	scoring='r2',
	n_jobs=-1
)

print("--- Random Forest Tuning ---")
print("Starting model training...")
grid.fit(X, y_log)

print(f"Best Parameters: {grid.best_params_}")
print(f"Best CV R-squared: {grid.best_score_:.4f}")
