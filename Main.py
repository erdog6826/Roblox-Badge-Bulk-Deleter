import os
import sys
import time
import requests

from dotenv import load_dotenv

load_dotenv()

roblox_token = os.environ.get("ROBLOSECURITY")
user_id = os.environ.get("USERID")

if not roblox_token or not user_id:
    print("ROBLOSECURITY and USERID are required.")
    sys.exit(1)

def main():
    s = requests.Session()

    # Set Roblox cookie
    s.cookies[".ROBLOSECURITY"] = roblox_token

    # Get CSRF token
    csrf = s.post("https://auth.roblox.com/v2/logout")

    if "X-CSRF-TOKEN" in csrf.headers:
        s.headers["X-CSRF-TOKEN"] = csrf.headers["X-CSRF-TOKEN"]
    else:
        print("Failed to get CSRF token.")
        print(csrf.status_code)
        print(csrf.text)
        sys.exit(1)

    badge_ids = []
    cursor = ""
    page = 0

    print("Fetching badges...")

    while True:
        url = (
            f"https://badges.roblox.com/v1/users/{user_id}/badges"
            f"?sortOrder=Desc&limit=100&cursor={cursor}"
        )

        r = s.get(url)

        if r.status_code != 200:
            print("Failed fetching badges.")
            print(r.status_code)
            print(r.text)
            return

        content = r.json()

        data = content.get("data", [])
        cursor = content.get("nextPageCursor")

        for badge in data:
            badge_ids.append(badge["id"])

        page += 1

        print(f"Fetched page #{page} | Total badges: {len(badge_ids)}")

        if not cursor:
            break

    total = len(badge_ids)

    print(f"\nFound {total} badges.")
    print("Deleting badges...\n")

    deleted = 0

    for badge_id in badge_ids:
        url = f"https://badges.roblox.com/v1/user/badges/{badge_id}"

        while True:
            r = s.delete(url)

            # Refresh CSRF token if needed
            if r.status_code == 403 and "X-CSRF-TOKEN" in r.headers:
                s.headers["X-CSRF-TOKEN"] = r.headers["X-CSRF-TOKEN"]
                continue

            # Rate limited
            if r.status_code == 429:
                print(f"Rate limited on badge #{badge_id}. Waiting 10 seconds...")
                time.sleep(10)
                continue

            break

        if r.status_code == 200:
            deleted += 1
            print(f"Deleted badge #{badge_id} ({deleted}/{total})")
        else:
            print(f"\nFailed to delete badge #{badge_id}")
            print(f"Status: {r.status_code}")
            print(f"Response: {r.text}\n")

        # Slow down requests
        time.sleep(2)

    print(f"\nFinished. Deleted {deleted}/{total} badges.")

if __name__ == "__main__":
    main()
