import logging
import json

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log request details
        print(f"=== REQUEST === {request.method} {request.path}")
        print(f"Content-Type: {request.headers.get('Content-Type', 'Not set')}")
        print(f"Accept: {request.headers.get('Accept', 'Not set')}")
        
        if request.body:
            try:
                body_str = request.body.decode('utf-8')
                print(f"Body: {body_str[:500]}")
            except:
                print(f"Body: {request.body[:500]}")
        
        response = self.get_response(request)
        
        print(f"=== RESPONSE === {response.status_code}")
        if response.status_code >= 400:
            try:
                content = response.content.decode('utf-8')
                print(f"Error content: {content[:500]}")
            except:
                print(f"Error content: {response.content[:500]}")
        
        return response