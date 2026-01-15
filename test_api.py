#!/usr/bin/env python3
"""
MDRS Test Script
Tests all API endpoints with sample data
"""
import requests
import json
from io import BytesIO
from PIL import Image

API_BASE = "http://localhost:8000"

def test_health_check():
    """Test API health endpoint"""
    print("🔍 Testing health check...")
    response = requests.get(f"{API_BASE}/")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    print()

def test_text_analysis():
    """Test text analysis"""
    print("🔍 Testing text analysis...")
    data = {
        'text': "BREAKING: You won't believe this SHOCKING news! URGENT - must see immediately!!!",
        'source': 'Social Media',
        'context': 'Viral post'
    }
    response = requests.post(f"{API_BASE}/analyze/text", data=data)
    print(f"   Status: {response.status_code}")
    result = response.json()
    print(f"   Risk Score: {result['risk_score']}/100")
    print(f"   Risk Level: {result['risk_level']}")
    print(f"   Signals Detected: {result['signals_detected']}")
    print()

def test_image_analysis():
    """Test image analysis with generated image"""
    print("🔍 Testing image analysis...")
    
    # Create a test image
    img = Image.new('RGB', (1920, 1080), color='red')
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    files = {'file': ('test_image.png', img_byte_arr, 'image/png')}
    data = {'source': 'Test', 'context': 'Generated image'}
    
    response = requests.post(f"{API_BASE}/analyze/image", files=files, data=data)
    print(f"   Status: {response.status_code}")
    result = response.json()
    print(f"   Risk Score: {result['risk_score']}/100")
    print(f"   Risk Level: {result['risk_level']}")
    print(f"   Signals Detected: {result['signals_detected']}")
    print()

def main():
    print("=" * 60)
    print("MDRS API Test Suite")
    print("=" * 60)
    print()
    
    try:
        # Test health check
        test_health_check()
        
        # Test text analysis
        test_text_analysis()
        
        # Test image analysis
        test_image_analysis()
        
        print("=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to backend server.")
        print("   Make sure the backend is running on http://localhost:8000")
        print("   Run: cd backend && python main.py")
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    main()
