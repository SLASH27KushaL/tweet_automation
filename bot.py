import os
import time
import google.generativeai as genai
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Load environment variables
load_dotenv()
EMAIL = os.getenv("TWITTER_EMAIL")
USERNAME = os.getenv("TWITTER_USERNAME")  # Without @ symbol
PASSWORD = os.getenv("TWITTER_PASSWORD")
PHONE_NUMBER = os.getenv("TWITTER_PHONE")  # For SMS-based verification if needed
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

def generate_tech_tweet():
    """Generate a tech-related tweet using Gemini AI"""
    prompt = (
        "Write a short, engaging tweet about programming, tech, or AI. "
        "Keep it casual and human-like. No hashtags or links. "
        "Maximum 280 characters."
    )
    try:
        response = model.generate_content(prompt)
        tweet = response.text.strip()
        print("🧠 Generated Tweet:\n", tweet)
        return tweet
    except Exception as e:
        print("❌ Gemini Error:", e)
        return "Just had one of those coding breakthroughs after hours of struggle. The best feeling!"

def twitter_login(driver):
    """Handle the complete Twitter login process with one-pass security verification."""
    wait = WebDriverWait(driver, 20)
    print("\n🔐 Starting Twitter login process...")
    
    # Navigate to login page
    driver.get("https://twitter.com/i/flow/login")
    time.sleep(3)

    # Step 1: Enter email/username
    print("📧 Entering email/username...")
    user_field = wait.until(EC.visibility_of_element_located(
        (By.XPATH, '//input[@autocomplete="username" or contains(@aria-label, "username") or contains(@aria-label, "email") or contains(@aria-label, "Phone")]')
    ))
    user_field.send_keys(EMAIL + Keys.ENTER)
    time.sleep(2)

    # Step 2: One-pass security verification
    inputs = driver.find_elements(By.XPATH, '//input[@data-testid="ocfEnterTextTextInput"]')
    if inputs:
        verification_field = inputs[0]
        label_text = ""
        try:
            label = driver.find_element(By.XPATH,
                f'//label[@for="{verification_field.get_attribute("id")}"]')
            label_text = label.text.lower()
        except:
            label_text = (verification_field.get_attribute("aria-label") or "").lower()
        
        print(f"🛡️ Security field detected: `{label_text or 'unclear'}`")
        # Decide which credential to send
        if "username" in label_text:
            to_send = USERNAME
        elif "email" in label_text:
            to_send = EMAIL
        elif "phone" in label_text:
            to_send = PHONE_NUMBER
        else:
            to_send = USERNAME
        verification_field.send_keys(to_send + Keys.ENTER)
        time.sleep(2)
    else:
        print("ℹ️ No extra security step detected.")

    # Step 3: Enter password
    print("🔑 Entering password...")
    password_field = wait.until(EC.visibility_of_element_located(
        (By.XPATH, '//input[@autocomplete="current-password"]')
    ))
    password_field.send_keys(PASSWORD + Keys.ENTER)
    time.sleep(3)

    # Verify successful login
    wait.until(EC.url_contains("home"))
    print("✅ Login successful!")

def post_tweet(driver, tweet_text):
    """Compose and post a tweet with comprehensive debugging"""
    wait = WebDriverWait(driver, 20)
    print("\n✍️ Starting tweet composition...")
    
    try:
        # Open tweet composer
        driver.get("https://twitter.com/compose/tweet")
        time.sleep(3)
        
        # DEBUG: Print page title and URL
        print(f"Current page: {driver.title} | {driver.current_url}")
        
        # Find tweet box
        tweet_box = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//div[@data-testid='tweetTextarea_0'] | //div[@role='textbox']")
        ))
        tweet_box.click()
        
        # Type tweet with human-like pacing
        print("⌨️ Typing tweet...")
        for char in tweet_text:
            tweet_box.send_keys(char)
            time.sleep(0.05)
        
        # DEBUG: Print all buttons on page
        print("\n🔍 Listing all buttons on page:")
        all_buttons = driver.find_elements(By.XPATH, "//div[@role='button'] | //button")
        for i, btn in enumerate(all_buttons[:20]):  # Limit to first 20 buttons
            try:
                btn_text = btn.text.strip()[:50]  # Limit text length
                btn_id = btn.get_attribute("id") or "none"
                btn_testid = btn.get_attribute("data-testid") or "none"
                btn_class = btn.get_attribute("class")[:50] if btn.get_attribute("class") else "none"
                print(f"Button {i+1}: Text='{btn_text}' | ID='{btn_id}' | TestID='{btn_testid}' | Class='{btn_class}'")
            except:
                print(f"Button {i+1}: Could not inspect")
        
        # Try to find and click the post button
        print("\n🔎 Searching for post button...")
        post_button = None
        
        # Try multiple possible selectors
        button_selectors = [
            "//div[@data-testid='tweetButton']",
            "//div[@data-testid='tweetButtonInline']",
            "//div[@role='button' and contains(., 'Post')]",
            "//div[@role='button' and contains(., 'Tweet')]",
            "//button[contains(., 'Post')]",
            "//button[contains(., 'Tweet')]",
            "//span[contains(., 'Post')]/ancestor::div[@role='button']",
            "//span[contains(., 'Tweet')]/ancestor::div[@role='button']"
        ]
        
        for selector in button_selectors:
            try:
                post_button = driver.find_element(By.XPATH, selector)
                print(f"✅ Found button using selector: {selector}")
                print(f"Button details - Text: '{post_button.text}', ID: '{post_button.get_attribute('id')}', TestID: '{post_button.get_attribute('data-testid')}'")
                break
            except:
                continue
                
        if post_button:
            print("🖱️ Attempting to click post button...")
            try:
                # Scroll into view and click using JavaScript
                driver.execute_script("arguments[0].scrollIntoView(true);", post_button)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", post_button)
                print("✅ JavaScript click executed")
            except Exception as e:
                print(f"❌ JavaScript click failed: {e}")
                try:
                    post_button.click()
                    print("✅ Regular click executed")
                except Exception as e:
                    print(f"❌ Regular click failed: {e}")
                    raise
        else:
            print("❌ Could not find post button")
            raise Exception("Post button not found")
        
        # Verify tweet was posted
        try:
            wait.until(EC.presence_of_element_located(
                (By.XPATH, "//span[contains(text(), 'Your post was sent') or contains(text(), 'Your Tweet was sent')]")
            ))
            print("✅ Tweet posted successfully!")
        except:
            print("⚠️ Could not verify tweet was posted - may still have succeeded")
        
    except Exception as e:
        print(f"❌ Error posting tweet: {str(e)}")
        driver.save_screenshot("tweet_error.png")
        print("📸 Screenshot saved as tweet_error.png")
        raise

def main():
    """Main execution flow"""
    print("🚀 Twitter Auto-Poster Starting...")
    
    # Generate tweet
    tweet_content = generate_tech_tweet()
    
    # Set up browser
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    
    driver = None
    try:
        driver = uc.Chrome(options=options, use_subprocess=True)
        
        # Login to Twitter
        twitter_login(driver)
        
        # Post the generated tweet
        post_tweet(driver, tweet_content)
        
    except Exception as e:
        print(f"❌ Critical Error: {e}")
        if driver:
            try:
                driver.save_screenshot("main_error.png")
                print("📸 Screenshot saved as main_error.png")
            except:
                pass
    finally:
        if driver:
            try:
                time.sleep(2)
                driver.quit()
            except:
                pass
        print("\n🛑 Script completed.")

if __name__ == "__main__":
    main()