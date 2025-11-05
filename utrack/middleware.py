import json

class RequestResponseLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Print Request info
        print(f"\n🔴 [REQUEST] {request.method} {request.get_full_path()}")
        
        # Try to print request body
        if request.body:
            try:
                body_str = request.body.decode('utf-8')
                # Try to pretty print if it's JSON
                try:
                    body_json = json.loads(body_str)
                    print(f"📦 Body: {json.dumps(body_json, indent=2)}")
                except json.JSONDecodeError:
                    print(f"📦 Body: {body_str}")
            except Exception:
                print("📦 Body: (binary or non-utf8)")

        response = self.get_response(request)

        # Print Response info
        print(f"🟢 [RESPONSE] Status: {response.status_code}")
        
        # Try to print response content
        if hasattr(response, 'content'):
            try:
                content_str = response.content.decode('utf-8')
                # Try to pretty print if it's JSON
                try:
                    content_json = json.loads(content_str)
                    print(f"📦 Content: {json.dumps(content_json, indent=2)}")
                except json.JSONDecodeError:
                    print(f"📦 Content: {content_str[:500]}...") # Truncate if too long
            except Exception:
                print("📦 Content: (binary or non-utf8)")
        
        return response




