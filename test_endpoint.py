#!/usr/bin/env python
"""Simple script to test an endpoint and display the response."""
import requests
import json
import sys
from datetime import datetime

def test_endpoint(url, method='GET', headers=None, data=None):
    """
    Test an endpoint and display the response.
    
    Usage:
        python test_endpoint.py <url> [method] [--headers '{"key": "value"}'] [--data '{"key": "value"}']
    """
    try:
        # Default headers
        if headers is None:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        
        print(f"\n{'='*60}")
        print(f"Testing Endpoint: {method} {url}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        # Make request
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, timeout=10)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method.upper() == 'PATCH':
            response = requests.patch(url, headers=headers, json=data, timeout=10)
        elif method.upper() == 'PUT':
            response = requests.put(url, headers=headers, json=data, timeout=10)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=10)
        else:
            print(f"Error: Unsupported method {method}")
            return
        
        # Display response
        print(f"Status Code: {response.status_code}")
        print(f"Status: {response.reason}")
        print(f"\nHeaders:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        print(f"\nResponse Body:")
        print(f"{'-'*60}")
        
        # Try to parse as JSON
        try:
            json_data = response.json()
            print(json.dumps(json_data, indent=2, ensure_ascii=False))
        except:
            # If not JSON, print as text
            print(response.text)
        
        print(f"{'-'*60}\n")
        
        return response
        
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_endpoint.py <url> [method] [--headers '...'] [--data '...']")
        print("\nExamples:")
        print("  python test_endpoint.py http://localhost:8000/api/workout/list/")
        print("  python test_endpoint.py http://localhost:8000/api/workout/123/summary/ GET")
        print("  python test_endpoint.py http://localhost:8000/api/workout/create/ POST --data '{\"title\": \"Test\"}'")
        sys.exit(1)
    
    url = sys.argv[1]
    method = sys.argv[2] if len(sys.argv) > 2 else 'GET'
    
    headers = None
    data = None
    
    # Parse optional arguments
    i = 3
    while i < len(sys.argv):
        if sys.argv[i] == '--headers' and i + 1 < len(sys.argv):
            headers = json.loads(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--data' and i + 1 < len(sys.argv):
            data = json.loads(sys.argv[i + 1])
            i += 2
        else:
            i += 1
    
    test_endpoint(url, method, headers, data)

