from flask import Flask

app = Flask(__name__)

@app.route('/scan/start', methods=['GET'])
def start_scan():
    pass

@app.route('/scan/{scan_id}/add', methods=['POST'])
def add_image(scan_id):
    pass

@app.route('/scan/{scan_id}/confirm', methods=['POST'])
def confirm_scan(scan_id):
    pass

if __name__ == '__main__':
    app.run('0.0.0.0', debug=True)