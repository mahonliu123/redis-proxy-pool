from flask import Flask, g
from db import RedisClient


__all__ = ['app']

app =Flask(__name__)

def get_conn():

    if not hasattr(g, 'redis_client'):
        g.redis_client = RedisClient()
    return g.redis_client

@app.route('/')
def index():
    return '<h2>Welcome to Proxy Pool System</h2>'

@app.route('/get')
def get_proxy():
    conn = get_conn()
    return conn.get_proxy()

@app.route('/count')
def get_count():
    conn = get_conn()
    return conn.get_proxy_count()

if __name__ == '__main__':
    app.run()