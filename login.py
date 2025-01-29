from playwright.sync_api import sync_playwright
import time

def login_to_x(username, email, password, user_data_dir="./chrome-data"):
    with sync_playwright() as playwright:
        # Launch persistent context
        browser = playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
        )
        page = browser.new_page()
        
        # Go to login page
        page.goto('https://twitter.com/login')
        time.sleep(2)
        
        # Enter username
        page.fill('input[autocomplete="username"]', username)
        page.click('text=Next')
        time.sleep(2)
        
        # Check which screen appears next - password or verification
        try:
            # First check if password field is visible
            if page.locator('input[type="password"]').is_visible(timeout=3000):
                print("Password field found, entering password...")
                page.fill('input[type="password"]', password)
                page.click('text=Log in')
                time.sleep(2)
                
                # Check for confirmation code input
                if page.locator('input[data-testid="ocfEnterTextTextInput"]').is_visible(timeout=3000):
                    print("Confirmation code required!")
                    confirmation_code = input("Please check your email and enter the confirmation code: ")
                    page.fill('input[data-testid="ocfEnterTextTextInput"]', confirmation_code)
                    page.click('text=Next')
            else:
                # If no password field, look for email/phone verification
                print("Verification required, entering email...")
                page.fill('input[data-testid="ocfEnterTextTextInput"]', email)
                page.click('text=Next')
                
                # Now enter password
                page.fill('input[type="password"]', password)
                page.click('text=Log in')
        except Exception as e:
            print(f"Error during login: {e}")
        
        print("Login successful! You can close this window once you're fully logged in.")
        input("Press Enter to close the browser...")
        browser.close()

if __name__ == "__main__":
    username = input("Enter your username: ")
    email = input("Enter your email: ")
    password = input("Enter your password: ")
    login_to_x(username, email, password) 