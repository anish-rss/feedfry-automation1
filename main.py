from playwright.sync_api import sync_playwright

# List of URLs to generate RSS feeds for
TARGET_URLS = [
    "https://www.thelayoff.com/resmed",
    "https://boxden.com/forumdisplay.php?f=218"
]

def create_feeds():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)

        for url in TARGET_URLS:
            print(f"\n🔍 Processing: {url}")
            context = browser.new_context()
            page = context.new_page()
            try:
                # Visit Feedfry
                page.goto("https://feedfry.com", timeout=60000)

                # Input URL and trigger event
                form = page.locator('form[action="/preview"]')
                url_input = form.locator('input#url')
                url_input.click()
                url_input.fill("")
                url_input.type(url)
                url_input.press("Enter")
                print("👉 URL field typed and triggered.")
                page.wait_for_timeout(2000)

                # Click submit
                form.locator('button[type="submit"]').nth(1).click()
                page.wait_for_timeout(3000)

                # Try clicking "Version 1"
                version1_button = page.locator('#version_1 form button').first
                try:
                    version1_button.wait_for(state="visible", timeout=10000)
                    version1_button.click()
                    print("📰 Clicked Version 1 button.")
                    page.wait_for_timeout(3000)
                except:
                    print("⚠️ 'Version 1' not available, checking if redirected to feed page...")

                # Look for RSS feed input field
                rss_input = page.locator("input.form-control").first
                rss_url = rss_input.input_value()

                if rss_url and rss_url.startswith("http"):
                    print(f"✅ RSS feed for {url}:\n{rss_url}")
                else:
                    print(f"❌ No RSS feed found for {url}")

            except Exception as e:
                print(f"❌ Error processing {url}: {e}")
            finally:
                context.close()

        browser.close()

if __name__ == "__main__":
    create_feeds()
