#!/usr/bin/env python3
"""
Test script for the /rephrase endpoint

This script demonstrates how to use the new /rephrase endpoint that:
1. Calls the executor to access BlackBox content and resources
2. Regenerates content while preserving the original content ID
3. Updates MongoDB with the regenerated content under the same ID
"""

import asyncio
import httpx
import json

async def test_rephrase_endpoint():
    """Test the /rephrase endpoint functionality"""
    
    base_url = "http://localhost:8001"
    
    # Example content ID (you'll need a real one from your MongoDB)
    test_content_id = "507f1f77bcf86cd799439011"  # Replace with actual content ID
    
    # Test payload
    payload = {
        "content_id": test_content_id,
        "instructions": "Make this content more engaging and add emojis. Focus on professional tone while being accessible."
    }
    
    print("Testing /rephrase endpoint...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/rephrase",
                json=payload,
                timeout=30.0
            )
            
            print(f"\nResponse Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"\nSuccess! Response:")
                print(json.dumps(result, indent=2))
                
                # Verify the ID is preserved
                if result.get("id") == test_content_id:
                    print(f"✅ Content ID preserved: {result['id']}")
                else:
                    print(f"❌ Content ID not preserved! Expected: {test_content_id}, Got: {result.get('id')}")
                    
                print(f"✅ Content regenerated with status: {result.get('status')}")
                print(f"✅ Message: {result.get('message')}")
                
            else:
                print(f"\nError! Response:")
                print(response.text)
                
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")

async def test_content_specific_rephrase():
    """Test the content/{content_id}/rephrase endpoint for comparison"""
    
    base_url = "http://localhost:8001"
    test_content_id = "507f1f77bcf86cd799439011"  # Replace with actual content ID
    
    payload = {
        "instructions": "Make this content more professional and concise"
    }
    
    print("\n" + "="*50)
    print("Testing /content/{content_id}/rephrase endpoint for comparison...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/content/{test_content_id}/rephrase",
                json=payload,
                timeout=30.0
            )
            
            print(f"\nResponse Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"\nSuccess! Response:")
                print(json.dumps(result, indent=2))
            else:
                print(f"\nError! Response:")
                print(response.text)
                
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting rephrase endpoint tests...")
    print("Make sure the backend server is running on localhost:8001")
    print("Also ensure you have valid content in MongoDB with the test content ID")
    
    asyncio.run(test_rephrase_endpoint())
    asyncio.run(test_content_specific_rephrase())
    
    print("\n✨ Tests completed!")
