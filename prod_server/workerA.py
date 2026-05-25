from celery import Celery
import joblib
import pandas as pd
import numpy as np

# Load model files
model = joblib.load('star_predictor_model.pkl')
top_languages = joblib.load('top_languages.pkl')
expected_columns = joblib.load('model_columns.pkl')

# Load data file
DATA_FILE = 'model_scoring_data.csv'

# Celery configuration
CELERY_BROKER_URL = 'amqp://rabbitmq:rabbitmq@rabbit:5672/'
CELERY_RESULT_BACKEND = 'rpc://'
# Initialize Celery
celery = Celery('workerA', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

@celery.task
def predict_and_rank_repos():
        # Load  data file
        df = pd.read_csv(DATA_FILE)

        # Turn boolean features numerical
        bool_columns = ['has_wiki', 'has_pages', 'has_discussions', 'archived']
        df[bool_columns] = df[bool_columns].astype(int)

        # Handle language feature
        df['language'] = df['language'].fillna('Other')
        df['language'] = df['language'].apply(lambda x: x if x in top_languages else 'Other')
        df_encoded = pd.get_dummies(df, columns=['language'], drop_first=False)

        # Drop repo_name and stars
        X = df_encoded.drop(['repo_name', 'stars'], axis=1)

        X = X.reindex(columns=expected_columns, fill_value=0)
        # Create predictions
        predicted_stars_log = model.predict(X)
        predicted_stars = np.expm1(predicted_stars_log)

        # result df
        results_df = pd.DataFrame({
                'repo_name': df['repo_name'],
                'actual_stars': df['stars'],
                'predicted_stars': predicted_stars.astype(int)
        })

        # rank the result
        ranked_results = results_df.sort_values(by='predicted_stars', ascending=False)

        return ranked_results.to_dict(orient='records')
