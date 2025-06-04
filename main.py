import smtplib
from email.mime.text import MIMEText
import os
from playwright.sync_api import sync_playwright

# Load credentials from GitHub Secrets
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")
TO_EMAIL = os.environ.get("TO_EMAIL")

# Target URLs to generate RSS feeds for
TARGET_URLS = [
    "https://www.thelayoff.com/resmed",
    "https://boxden.com/forumdisplay.php?f=218"
]

def send_email(body):
    msg = MIMEText(body)
    msg["Subject"] = "Your Weekly RSS Feeds"
    msg["From"] = EMAIL_USER
    msg["To"] = TO_EMAIL

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)

def create_feeds():
    message = ""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # ✅ Headless for GitHub Actions
        for url in TARGET_URLS:
            print(f"\n🔍 Processing: {url}")
            context = browser.new_context()
            page = context.new_page()
            try:
                # Open Feedfry
                page.goto("https://feedfry.com", timeout=60000)

                # Fill the form properly
                form = page.locator('form[action="/preview"]')
                url_input = form.locator('input#url')
                url_input.click()
                url_input.fill("")
                url_input.type(url)
                url_input.press("Enter")
                print("👉 URL typed and triggered.")
                page.wait_for_timeout(2000)

                # Submit the form
                form.locator("button[type='submit']").nth(1).click()  # ✅ Corrected quote syntax
                page.wait_for_timeout(3000)

                # Try to click Version 1 if available
                version1_button = page.locator('#version_1 form button').first
                try:
                    version1_button.wait_for(state="visible", timeout=10000)
                    version1_button.click()
                    print("📰 Clicked Version 1 button.")
                    page.wait_for_timeout(3000)
                except:
                    print("⚠️ 'Version 1' not available — checking for direct feed page...")

                # Extract the RSS URL
                rss_input = page.locator("input.form-control").first
                rss_url = rss_input.input_value()

                if rss_url and rss_url.startswith("http"):
                    print(f"✅ RSS for {url}:\n{rss_url}")
                    message += f"{url}\n{rss_url}\n\n"
                else:
                    print(f"❌ No RSS feed found for {url}")
                    message += f"{url}\nERROR: No RSS feed found\n\n"

            except Exception as e:
                print(f"❌ Error processing {url}: {e}")
                message += f"{url}\nERROR: {e}\n\n"
            finally:
                context.close()

        browser.close()

    # Send the email if any results collected
    if message.strip():
        print("\n📧 Sending email with results...")
        send_email(message)
        print("✅ Email sent.")
    else:
        print("⚠️ No results to email.")

if __name__ == "__main__":
    create_feeds()
