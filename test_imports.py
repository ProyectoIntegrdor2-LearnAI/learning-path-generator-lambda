"""
Test script to identify which import is causing the timeout
"""
import json
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    results = {}
    
    # Test 1: Basic imports
    try:
        logger.info("Testing basic imports...")
        import os
        import time
        results["basic_imports"] = "✓ OK"
    except Exception as e:
        results["basic_imports"] = f"✗ ERROR: {str(e)}"
        
    # Test 2: NumPy
    try:
        logger.info("Testing numpy import...")
        import numpy as np
        results["numpy"] = "✓ OK"
    except Exception as e:
        results["numpy"] = f"✗ ERROR: {str(e)}"
        
    # Test 3: Boto3
    try:
        logger.info("Testing boto3 import...")
        import boto3
        results["boto3"] = "✓ OK"
    except Exception as e:
        results["boto3"] = f"✗ ERROR: {str(e)}"
        
    # Test 4: psycopg2
    try:
        logger.info("Testing psycopg2 import...")
        import psycopg2
        results["psycopg2"] = "✓ OK"
    except Exception as e:
        results["psycopg2"] = f"✗ ERROR: {str(e)}"
        
    # Test 5: pymongo
    try:
        logger.info("Testing pymongo import...")
        from pymongo import MongoClient
        results["pymongo"] = "✓ OK"
    except Exception as e:
        results["pymongo"] = f"✗ ERROR: {str(e)}"
        
    # Test 6: utils modules
    try:
        logger.info("Testing utils.bedrock_client import...")
        sys.path.insert(0, '/var/task/src')
        from utils.bedrock_client import get_bedrock_client
        results["bedrock_client"] = "✓ OK"
    except Exception as e:
        results["bedrock_client"] = f"✗ ERROR: {str(e)}"
        
    try:
        logger.info("Testing utils.mongodb_client import...")
        from utils.mongodb_client import get_mongo_client
        results["mongodb_client"] = "✓ OK"
    except Exception as e:
        results["mongodb_client"] = f"✗ ERROR: {str(e)}"
        
    try:
        logger.info("Testing utils.postgres_client import...")
        from utils.postgres_client import get_postgres_client
        results["postgres_client"] = "✓ OK"
    except Exception as e:
        results["postgres_client"] = f"✗ ERROR: {str(e)}"
        
    return results

def lambda_handler(event, context):
    logger.info("========== STARTING IMPORT TEST ==========")
    results = test_imports()
    logger.info(f"Import test results: {json.dumps(results, indent=2)}")
    
    return {
        "statusCode": 200,
        "body": json.dumps(results, indent=2)
    }

if __name__ == "__main__":
    print(lambda_handler({}, None))
