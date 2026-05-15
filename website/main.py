from app import create_app
import argparse

app = create_app()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1', help='Host to run the server on')
    parser.add_argument('--port', default=5001, type=int, help='Port to run the server on')
    args = parser.parse_args()
    app.run(debug=True, host=args.host, port=args.port)
else:
    gunicorn_app = app