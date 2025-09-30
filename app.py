"""
Wrapper to support both app.py and hair_color_server.py naming
"""
from hair_color_server import app

if __name__ == '__main__':
    app.run()