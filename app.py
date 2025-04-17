from flask import Flask, redirect

app = Flask(__name__)

@app.route('/')
def index():
    # Redirect to the Streamlit UI which is running on the /proxy/8000 path
    return redirect('/proxy/8000')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)