import pandas as pd
import numpy as np
import joblib
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor

# Load Data
df = pd.read_csv('../data/model_train_data.csv')

# Fix Boolean Columns
bool_columns = ['has_wiki', 'has_pages', 'has_discussions', 'archived']
df[bool_columns] = df[bool_columns].astype(int)

# Handle Language
TOP_N = 5 
top_languages = df['language'].value_counts().nlargest(TOP_N).index.tolist()
df['language'] = df['language'].fillna('Other')
df['language'] = df['language'].apply(lambda x: x if x in top_languages else 'Other')

df_encoded = pd.get_dummies(df, columns=['language'], drop_first=False)

# Split data into features and target. Convert y to log_scale for power law
X = df_encoded.drop(['repo_name', 'stars'], axis=1)
y_log = np.log1p(df_encoded['stars'])

# Build the pipeline with the best model and hyperparameters
final_model = Pipeline([
    ('scaler', StandardScaler()),
    ('model', RandomForestRegressor(max_depth=10, n_estimators=200, random_state=42))
])

print("Training final Random Forest production model...")
final_model.fit(X, y_log)

# Save Everything
joblib.dump(final_model, 'star_predictor_model.pkl')
joblib.dump(top_languages, 'top_languages.pkl')
joblib.dump(X.columns.tolist(), 'model_columns.pkl')
