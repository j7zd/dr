from flask import Flask, render_template, request
import requests

app = Flask(__name__)

@app.route('/callback_test', methods=['POST'])
def callback_test():
    json = request.json
    # save to json file
    with open('callback_test.json', 'w') as f:
        json.dump(json, f)

    return 'OK'

@app.route('/test_page')
def test_page():
    r = requests.post('http://localhost:5000/api/verification/start', json={
        'callback_url': 'http://localhost:5001/callback_test',
        'requested_information': 'full_name;date_of_birth'
    })
    session_id = r.json()['session_id']
    return render_template('test_page.html', session_id=session_id)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)

