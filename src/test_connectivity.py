"""
Simple connectivity test for Lambda
Tests if Lambda can reach external services
"""
import json
import socket
import time
from urllib import request
from urllib.error import URLError


def lambda_handler(event, context):
    results = {
        "timestamp": time.time(),
        "tests": {}
    }
    
    # Test 1: DNS Resolution
    print("Testing DNS resolution...")
    try:
        ip = socket.gethostbyname("www.google.com")
        results["tests"]["dns"] = {"status": "✓ OK", "ip": ip}
        print(f"DNS OK: www.google.com -> {ip}")
    except Exception as e:
        results["tests"]["dns"] = {"status": "✗ FAILED", "error": str(e)}
        print(f"DNS FAILED: {str(e)}")
    
    # Test 2: HTTP Request (with timeout)
    print("Testing HTTP request to example.com...")
    try:
        req = request.Request("http://example.com")
        with request.urlopen(req, timeout=5) as response:
            status = response.status
            results["tests"]["http"] = {"status": "✓ OK", "http_status": status}
            print(f"HTTP OK: Status {status}")
    except URLError as e:
        results["tests"]["http"] = {"status": "✗ FAILED", "error": str(e)}
        print(f"HTTP FAILED: {str(e)}")
    except socket.timeout:
        results["tests"]["http"] = {"status": "✗ TIMEOUT", "error": "Connection timed out after 5s"}
        print("HTTP TIMEOUT after 5s")
    
    # Test 3: HTTPS Request
    print("Testing HTTPS request to www.google.com...")
    try:
        req = request.Request("https://www.google.com")
        with request.urlopen(req, timeout=5) as response:
            status = response.status
            results["tests"]["https"] = {"status": "✓ OK", "http_status": status}
            print(f"HTTPS OK: Status {status}")
    except URLError as e:
        results["tests"]["https"] = {"status": "✗ FAILED", "error": str(e)}
        print(f"HTTPS FAILED: {str(e)}")
    except socket.timeout:
        results["tests"]["https"] = {"status": "✗ TIMEOUT", "error": "Connection timed out after 5s"}
        print("HTTPS TIMEOUT after 5s")
    
    # Test 4: MongoDB Atlas DNS
    print("Testing MongoDB Atlas DNS...")
    try:
        # Extract host from MongoDB URI if provided in event
        mongo_host = "projectcluster.zylt93p.mongodb.net"
        ip = socket.gethostbyname(mongo_host)
        results["tests"]["mongodb_dns"] = {"status": "✓ OK", "ip": ip}
        print(f"MongoDB DNS OK: {mongo_host} -> {ip}")
    except Exception as e:
        results["tests"]["mongodb_dns"] = {"status": "✗ FAILED", "error": str(e)}
        print(f"MongoDB DNS FAILED: {str(e)}")
    
    # Test 5: Bedrock endpoint DNS
    print("Testing Bedrock endpoint DNS...")
    try:
        bedrock_host = "bedrock-runtime.us-east-2.amazonaws.com"
        ip = socket.gethostbyname(bedrock_host)
        results["tests"]["bedrock_dns"] = {"status": "✓ OK", "ip": ip}
        print(f"Bedrock DNS OK: {bedrock_host} -> {ip}")
    except Exception as e:
        results["tests"]["bedrock_dns"] = {"status": "✗ FAILED", "error": str(e)}
        print(f"Bedrock DNS FAILED: {str(e)}")
    
    print("\n" + "="*50)
    print("CONNECTIVITY TEST RESULTS:")
    print(json.dumps(results, indent=2))
    print("="*50)
    
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(results, indent=2)
    }
