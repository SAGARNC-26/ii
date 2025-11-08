"""
Test Brute Force Protection
Demonstrates the IP blocking feature after 5 failed login attempts
"""

import requests
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
LOGIN_URL = f"{BASE_URL}/login"

def test_failed_logins():
    """Test multiple failed login attempts"""
    print("=" * 60)
    print("  Brute Force Protection Test")
    print("=" * 60)
    print()
    print("Testing 6 failed login attempts...")
    print("Expected: IP blocked after 5th attempt")
    print()
    
    session = requests.Session()
    
    for attempt in range(1, 7):
        print(f"\n[Attempt {attempt}] Trying wrong password...")
        
        try:
            response = session.post(
                LOGIN_URL,
                data={
                    'username': 'admin',
                    'password': 'wrongpassword'
                },
                allow_redirects=False
            )
            
            # Check response
            if response.status_code == 200:
                content = response.text.lower()
                
                if 'blocked' in content:
                    print(f"✓ IP BLOCKED after {attempt} attempts!")
                    print("  Block message displayed correctly")
                    
                    # Extract remaining time if visible
                    if 'minute' in content or 'second' in content:
                        print("  Countdown timer showing")
                    
                    return True
                    
                elif 'attempt' in content and 'remaining' in content:
                    # Extract attempts remaining
                    print(f"  Status: Failed login recorded")
                    print(f"  Message: Warnings displayed")
                    
                else:
                    print(f"  Status: Failed - no block yet")
            else:
                print(f"  Unexpected status code: {response.status_code}")
                
        except Exception as e:
            print(f"  Error: {e}")
            return False
        
        time.sleep(0.5)  # Small delay between attempts
    
    print("\n❌ Expected block after 5 attempts but didn't happen!")
    return False


def test_successful_after_block():
    """Test that valid login works after waiting for block to expire"""
    print("\n" + "=" * 60)
    print("  Testing Successful Login After Block Expires")
    print("=" * 60)
    print()
    print("Waiting for block to expire (5 minutes)...")
    print("This is a long test - you may want to skip it")
    print()
    
    # Wait for block to expire
    wait_time = 301  # 5 minutes + 1 second
    
    for remaining in range(wait_time, 0, -30):
        mins = remaining // 60
        secs = remaining % 60
        print(f"  Time remaining: {mins}m {secs}s", end='\r')
        time.sleep(30)
    
    print("\n\n[After Block] Trying correct password...")
    
    session = requests.Session()
    response = session.post(
        LOGIN_URL,
        data={
            'username': 'admin',
            'password': 'changeme'
        },
        allow_redirects=False
    )
    
    if response.status_code == 302 and '/dashboard' in response.headers.get('Location', ''):
        print("✓ Login successful after block expired!")
        return True
    else:
        print("❌ Login failed - block may still be active")
        return False


def check_blocked_ips_api():
    """Check the blocked IPs API endpoint"""
    print("\n" + "=" * 60)
    print("  Checking Blocked IPs API")
    print("=" * 60)
    print()
    
    # First login to get session
    session = requests.Session()
    response = session.post(
        LOGIN_URL,
        data={
            'username': 'admin',
            'password': 'changeme'
        }
    )
    
    if response.status_code != 200 or 'dashboard' not in response.url.lower():
        print("❌ Need to login first with correct credentials")
        return False
    
    # Check blocked IPs API
    api_url = f"{BASE_URL}/api/blocked_ips"
    response = session.get(api_url)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ API accessible")
        print(f"  Blocked IPs: {data.get('count', 0)}")
        
        if data.get('blocked_ips'):
            for ip_data in data['blocked_ips']:
                print(f"\n  IP: {ip_data['ip']}")
                print(f"  Attempts: {ip_data['attempts']}")
                print(f"  Blocked until: {ip_data['blocked_until']}")
                print(f"  Remaining: {ip_data['remaining_seconds']}s")
        else:
            print("  No IPs currently blocked")
        
        return True
    else:
        print(f"❌ API error: {response.status_code}")
        return False


def main():
    print("\n🔒 Smart Vault CCTV - Brute Force Protection Test")
    print()
    print("This script will test the brute force protection feature")
    print("by attempting multiple failed logins.")
    print()
    input("Press Enter to continue (make sure Flask server is running)...")
    print()
    
    # Test 1: Failed logins
    success1 = test_failed_logins()
    
    if success1:
        print("\n✅ Test 1 PASSED: IP blocking works correctly!")
    else:
        print("\n❌ Test 1 FAILED: IP blocking not working as expected")
    
    # Ask about Test 2 (takes 5 minutes)
    print()
    response = input("\nRun Test 2? (waits 5 mins for block to expire) [y/N]: ")
    
    if response.lower() == 'y':
        success2 = test_successful_after_block()
        if success2:
            print("\n✅ Test 2 PASSED: Login works after block expires!")
        else:
            print("\n❌ Test 2 FAILED: Login still blocked")
    else:
        print("\nSkipping Test 2 (block expiration test)")
    
    # Test 3: API check (if logged in)
    print()
    response = input("\nCheck Blocked IPs API? [y/N]: ")
    
    if response.lower() == 'y':
        success3 = check_blocked_ips_api()
        if success3:
            print("\n✅ Test 3 PASSED: API working correctly!")
        else:
            print("\n❌ Test 3 FAILED: API error")
    
    print("\n" + "=" * 60)
    print("  Test Complete!")
    print("=" * 60)
    print()
    print("📚 For more information, see: docs/brute_force_protection.md")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
