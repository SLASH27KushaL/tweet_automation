import os
import time
import random
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
USERNAME = os.getenv("TWITTER_USERNAME")
PASSWORD = os.getenv("TWITTER_PASSWORD")
PHONE_NUMBER = os.getenv("TWITTER_PHONE")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

def generate_multiple_tweets(count=3):
    """Generate multiple tweets on different topics."""
    tweets = []
    for _ in range(count):
        tweet = generate_topic_tweet()
        tweets.append(tweet)
        time.sleep(1)  # Small delay between generations
    return tweets

def generate_topic_tweet():
    """Generate a tweet on a randomly chosen topic."""
    topics = {
        "cricket": [
            "Write a funny or passionate tweet about cricket. Mention ongoing matches or legendary moments. Keep it under 280 characters.",
            "Write a tweet from the POV of a die-hard cricket fan during a nail-biter game. No hashtags or links.",
        ],
        "tech": [
            "Write a casual, relatable tweet about tech, coding, or AI. Include light humor or an 'aha' moment. Max 280 characters.",
            "Write a tweet on how programmers think. Keep it witty and engaging.",
        ],
        "us_politics": [
            "Write a sarcastic or witty tweet about recent US politics. Imagine it's a hot take on Twitter. No hashtags.",
            "Write a tweet about a current US political issue in a casual, opinionated tone — like a viral post.",
        ],
    }

    topic = random.choice(list(topics.keys()))
    prompt = random.choice(topics[topic])
    
    print(f"\n📌 Topic Chosen: {topic.capitalize()}")
    print(f"🎯 Prompt: {prompt}")

    try:
        response = model.generate_content(prompt)
        tweet = response.text.strip()
        print("🧠 Generated Tweet:\n", tweet)
        return tweet
    except Exception as e:
        print("❌ Gemini Error:", e)
        return "Just witnessed peak drama again — in code, cricket, and Congress. What a time to be alive."

def twitter_login(driver):
    """Login to Twitter with optional one-pass verification."""
    wait = WebDriverWait(driver, 20)
    print("\n🔐 Starting Twitter login process...")
    
    driver.get("https://twitter.com/i/flow/login")
    time.sleep(3)

    print("📧 Entering email/username...")
    user_field = wait.until(EC.visibility_of_element_located(
        (By.XPATH, '//input[@autocomplete="username"]')
    ))
    user_field.send_keys(EMAIL + Keys.ENTER)
    time.sleep(2)

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

    print("🔑 Entering password...")
    password_field = wait.until(EC.visibility_of_element_located(
        (By.XPATH, '//input[@autocomplete="current-password"]')
    ))
    password_field.send_keys(PASSWORD + Keys.ENTER)
    time.sleep(3)

    wait.until(EC.url_contains("home"))
    print("✅ Login successful!")

def post_tweet(driver, tweet_text):
    """Compose and post a tweet with fallback checks."""
    wait = WebDriverWait(driver, 20)
    print("\n✍️ Composing tweet...")
    
    try:
        driver.get("https://twitter.com/compose/tweet")
        time.sleep(3)
        
        print(f"Current page: {driver.title} | {driver.current_url}")
        
        tweet_box = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//div[@data-testid='tweetTextarea_0'] | //div[@role='textbox']")
        ))
        tweet_box.click()

        print("⌨️ Typing tweet...")
        for char in tweet_text:
            tweet_box.send_keys(char)
            time.sleep(0.05)

        print("\n🔎 Searching for post button...")
        post_button = None
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
                print(f"✅ Found button using: {selector}")
                break
            except:
                continue
        
        if post_button:
            print("🖱️ Clicking post button...")
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", post_button)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", post_button)
                print("✅ Tweet posted!")
            except Exception as e:
                print(f"❌ JS click failed: {e}")
                try:
                    post_button.click()
                except Exception as e:
                    print(f"❌ Fallback click failed: {e}")
                    raise
        else:
            print("❌ Post button not found.")
            raise Exception("Post button not found")

        try:
            wait.until(EC.presence_of_element_located(
                (By.XPATH, "//span[contains(text(), 'Your Tweet was sent')]")
            ))
            print("✅ Verified: Tweet sent.")
        except:
            print("⚠️ Tweet may have been sent — but not verified.")
        
    except Exception as e:
        print(f"❌ Tweeting Error: {str(e)}")
        driver.save_screenshot("tweet_error.png")
        print("📸 Screenshot saved as tweet_error.png")
        raise

def post_multiple_tweets(driver, tweets):
    """Post multiple tweets with delays between each."""
    for i, tweet in enumerate(tweets, 1):
        print(f"\n📢 Posting tweet {i} of {len(tweets)}")
        try:
            post_tweet(driver, tweet)
            # Random delay between tweets (3-7 seconds)
            delay = random.uniform(3, 7)
            print(f"⏳ Waiting {delay:.1f} seconds before next tweet...")
            time.sleep(delay)
        except Exception as e:
            print(f"❌ Failed to post tweet {i}: {e}")
            continue

def main():
    """Run the bot: generate tweets, log in, post all in headless Chrome."""
    print("🚀 Twitter Auto-Bot Starting...")

    # Generate multiple tweets (default is 3)
    tweets = generate_multiple_tweets(3)
    print(f"\n📝 Generated {len(tweets)} tweets to post:")

    options = uc.ChromeOptions()
    # Prevent detection
    options.add_argument("--disable-blink-features=AutomationControlled")
    # Run headless (no browser UI)
    options.add_argument("--headless=new")   # Chrome 109+ headless mode
    options.add_argument("--disable-gpu")
    # Sandbox flags
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = None
    try:
        driver = uc.Chrome(options=options, use_subprocess=True)
        twitter_login(driver)
        post_multiple_tweets(driver, tweets)
    except Exception as e:
        print(f"❌ Critical Error: {e}")
        if driver:
            driver.save_screenshot("main_error.png")
            print("📸 Screenshot saved as main_error.png")
    finally:
        if driver:
            time.sleep(2)
            driver.quit()
        print("🛑 Script completed.")

if __name__ == "__main__":
    main()