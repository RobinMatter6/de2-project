from workerA import predict_and_rank_repos

from flask import (
   Flask,
   request,
   jsonify,
   render_template
)

#app = Flask(__name__, template_folder='./templates',static_folder='./static')
app = Flask(__name__)

@app.route("/")
def index():
    return '''
        <h1>Group6</h1>
        <br>
        <form action="/predictions" method="GET">
                <button type="submit">Go to Predictions</button>
        </form>
        '''
@app.route("/predictions", methods=['POST', 'GET'])
def predictions():
    if request.method == 'POST':
        task = predict_and_rank_repos.delay()

        final_results = task.get()

        return render_template('result.html', final_results=final_results)

    return '''<form method="POST">
    <input type="submit" value="Predict & Rank">
    </form>'''

if __name__ == '__main__':
    app.run(host = '0.0.0.0',port=5100,debug=True, threaded=False)
