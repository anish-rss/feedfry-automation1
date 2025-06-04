from playwright.sync_api import sync_playwright
import smtplib
from email.mime.text import MIMEText

TARGET_URLS = [
    "https://www.thelayoff.com/resmed",
    "https://boxden.com/forumdisplay.php?f=218"
]

# Email setup
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_USER = "anish653931@gmail.com"
EMAIL_PASS = "jnob oinu salq bupj"
TO_EMAIL = "anish653931@gmail.com"

def send_email(body):
    msg = MIMEText(body)
    msg["Subject"] = "Your Weekly RSS Feeds"
    msg["From"] = EMAIL_USER
    msg["To"] = TO_EMAIL

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)

def create_feeds():
    message = ""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for url in TARGET_URLS:
            try:
                page.goto("https://feedfry.com", timeout=60000)
                form = page.locator('form[action="/preview"]')
                form.locator('input#url').fill(url)
                form.locator('button[type="submit"]').nth(1).click()
                page.wait_for_timeout(3000)

                version1_button = page.locator('#version_1 form button').nth(0)
                version1_button.wait_for(state="visible", timeout=10000)
                version1_button.click()
                page.wait_for_timeout(3000)

                rss_input = page.locator("input.form-control").first
                rss_url = rss_input.input_value()

                message += f"{url}\n{rss_url}\n\n"
            except Exception as e:
                message += f"{url}\nERROR: {e}\n\n"

        browser.close()

    send_email(message)

if __name__ == "__main__":
    create_feeds()
