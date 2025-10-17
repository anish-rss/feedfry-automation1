import smtplib
from email.mime.text import MIMEText
import os
from playwright.sync_api import sync_playwright
import xml.etree.ElementTree as ET
import urllib.request

# Load credentials from GitHub Secrets
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")
TO_EMAIL = os.environ.get("TO_EMAIL")
# Set DRY_RUN=true in Actions (or locally) to test without sending email
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"

# Target URLs to generate RSS feeds for (Boxden removed; 3x Rotten Tomatoes added)
TARGET_URLS = [
    "https://www.thelayoff.com/resmed",
    "https://www.rottentomatoes.com/browse/movies_in_theaters/sort:newest",
    "https://www.rottentomatoes.com/browse/movies_at_home/sort:newest",
    "https://www.rottentomatoes.com/browse/tv_series_browse/sort:newest"
]

def send_email(body: str) -> None:
    msg = MIMEText(body)
    msg["Subject"] = "Your Weekly RSS Feeds"
    msg["From"] = EMAIL_USER
    msg["To"] = TO_EMAIL

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)

def verify_feed(rss_url: str):
    """
    Fetch the generated RSS URL and try to parse minimal XML.
    Returns (ok: bool, detail: str).
    """
    try:
        req = urllib.request.Request(rss_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.status
            data = resp.read(2_000_000)  # limit to 2MB
        if status != 200:
            return False, f"HTTP {status}"
        try:
            root = ET.fromstring(data)
        except ET.ParseError as e:
            return False, f"XML parse error: {e}"
        tag = root.tag.lower()
        if "rss" in tag or "feed" in tag:  # RSS or Atom root
            return True, "Looks like a valid feed"
        return False, f"Unexpected root tag: {root.tag}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"

def create_feeds():
    message = "Feed verification results:\n\n"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        for url in TARGET_URLS:
            print(f"\n🔍 Processing: {url}")
            try:
                # Open Feedfry
                page.goto("https://feedfry.com", timeout=60000)

                # Fill the form
                form = page.locator('form[action="/preview"]')
                url_input = form.locator('input#url')
                url_input.click()
                url_input.fill("")
                url_input.type(url)
                url_input.press("Enter")
                print("👉 URL typed and triggered.")
                page.wait_for_timeout(2000)

                # Submit the form
                form.locator("button[type='submit']").nth(1).click()
                page.wait_for_timeout(3000)

                # Try "Version 1" if available
                version1_button = page.locator('#version_1 form button').first
                try:
                    version1_button.wait_for(state="visible", timeout=10000)
                    version1_button.click()
                    print("📰 Clicked Version 1 button.")
                    page.wait_for_timeout(3000)
                except:
                    print("⚠️ 'Version 1' not available — proceeding without it...")

                # Extract the RSS URL
                rss_input = page.locator("input.form-control").first
                rss_url = rss_input.input_value()

                if rss_url and rss_url.startswith("http"):
                    print(f"✅ RSS for {url}:\n{rss_url}")
                    ok, detail = verify_feed(rss_url)
                    status_emoji = "✅" if ok else "❌"
                    message += f"{url}\n{rss_url}\n{status_emoji} Live check: {detail}\n\n"
                else:
                    print(f"❌ No RSS feed found for {url}")
                    message += f"{url}\nERROR: No RSS feed found\n\n"

            except Exception as e:
                print(f"❌ Error processing {url}: {e}")
                message += f"{url}\nERROR: {e}\n\n"
            finally:
                # Reset the page between iterations
                page.goto("about:blank")
                page.wait_for_timeout(1000)

        context.close()
        browser.close()

    if message.strip():
        if DRY_RUN:
            print("\n🧪 DRY RUN enabled — not sending email. Output below:\n")
            print(message)
        else:
            print("\n📧 Sending email with results...")
            send_email(message)
            print("✅ Email sent.")
    else:
        print("⚠️ No results to email.")

if __name__ == "__main__":
    create_feeds()
