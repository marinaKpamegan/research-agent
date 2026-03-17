import requests

def test_json_login():
    url = "http://127.0.0.1:8000/api/auth/login"
    login_data = {
        "username": "testuser", # Assuming this user exists or you've just registered
        "password": "testpassword"
    }
    
    print(f"Testing JSON login at {url}...")
    try:
        response = requests.post(url, json=login_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")
        
        if response.status_code == 200:
            print("Login successful!")
            # Check for cookie
            if "access_token" in response.cookies:
                print("Access token cookie received.")
                
                # Test /me endpoint
                me_url = "http://127.0.0.1:8000/api/auth/me"
                me_response = requests.get(me_url, cookies=response.cookies)
                print(f"/me Status Code: {me_response.status_code}")
                print(f"/me Response: {me_response.json()}")
            else:
                print("Warning: access_token cookie NOT found in response.")
        elif response.status_code == 422:
            print("Error: Still getting 422 Unprocessable Content. JSON login might not be correctly handled.")
        else:
            print(f"Login failed with status {response.status_code}")
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_json_login()
