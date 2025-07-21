from asgiref.wsgi import WsgiToAsgi
from web_chat import app

# Convert Flask WSGI app to ASGI
asgi_app = WsgiToAsgi(app)

# This is what uvicorn will look for
application = asgi_app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("asgi:application", host="0.0.0.0", port=8000, reload=True) 