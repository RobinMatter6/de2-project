from sklearn.linear_model import LinearRegression
from sklearn.compose import TransformedTargetRegressor
from sklearn.model_selection import cross_val_score, KFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import pandas as pd
import numpy as np
# read datafile
df = pd.read_csv('../data/top_1000_github_repos_with_commits_v2.csv')

# Convert boolean features into numerical
bool_columns = ['has_wiki', 'has_pages', 'has_discussions', 'archived']
df[bool_columns] = df[bool_columns].astype(int)

# Number of languages to keep distinct
TOP_N = 5

# Find the TOP_N most frequent languages in the dataset
top_languages = df['language'].value_counts().nlargest(TOP_N).index.tolist()

# Replace any language not in the top N with "Other"
# We do this because one-hot encoding too many languages destroys performancy due to dimensionality
df['language'] = df['language'].fillna('Other')
df['language'] = df['language'].apply(lambda x: x if x in top_languages else 'Other')

# Now we do one-hot encoding on language to make it numerical
df_encoded = pd.get_dummies(df, columns=['language'], drop_first=False)

# Split data into features and target. Turn y into log_scale for power law.
X = df_encoded.drop(['repo_name', 'stars'], axis=1)
y_log = np.log1p(df_encoded['stars'])

# Create training pipeline
pipeline = Pipeline([
	('scaler', StandardScaler()),
	('model', LinearRegression())
])

# Make sure to shuffle data for CV
cv_strategy = KFold(n_splits=5, shuffle=True, random_state=42)

# Calculate scores
r2_scores = cross_val_score(pipeline, X, y_log, cv=cv_strategy, scoring='r2', n_jobs=-1)

print("--- Standard Linear Regression ---")
print(f"Average CV R-squared: {r2_scores.mean():.4f}")
