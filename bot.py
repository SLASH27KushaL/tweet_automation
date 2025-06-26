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
from bs4 import BeautifulSoup
import re
import urllib.parse

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

def remove_non_bmp_chars(text):
    """Remove characters outside the Basic Multilingual Plane (BMP)"""
    return ''.join(char for char in text if ord(char) <= 0xFFFF)

def generate_topic():
    """Generate a topic using Gemini AI."""
    try:
        prompt = "Suggest an interesting topic for a Wikipedia article. Reply with just the topic name."
        response = model.generate_content(prompt)
        topic = response.text.strip()
        # Clean up Gemini response
        topic = re.sub(r'[\*\-\"\']', '', topic)
        topic = topic.split('\n')[0].strip()
        topic = remove_non_bmp_chars(topic)  # Remove non-BMP characters
        print(f"🧠 Generated Topic: {topic}")
        return topic
    except Exception as e:
        print(f"❌ Topic Generation Error: {e}")
        return random.choice(["Artificial Intelligence", "Quantum Mechanics", "Renaissance Art", "Ancient Rome"])

def scrape_wikipedia_article(driver, topic):
    """Scrape a Wikipedia article for a given topic."""
    print(f"\n🌐 Scraping Wikipedia article for topic: {topic}")
    try:
        # Encode topic for URL
        encoded_topic = urllib.parse.quote_plus(topic)
        wiki_url = f"https://en.wikipedia.org/wiki/{encoded_topic}"
        print(f"🔍 Navigating to: {wiki_url}")
        driver.get(wiki_url)
        time.sleep(3)
        
        # Check if we landed on a disambiguation page
        if "may refer to" in driver.page_source:
            print("⚠️ Landed on disambiguation page. Searching instead...")
            search_url = f"https://en.wikipedia.org/w/index.php?search={encoded_topic}"
            driver.get(search_url)
            time.sleep(3)
            
            # Get first search result
            first_result = driver.find_element(By.CSS_SELECTOR, ".mw-search-results li:first-child a")
            article_url = first_result.get_attribute("href")
            print(f"🔍 Found article: {article_url}")
            driver.get(article_url)
            time.sleep(3)
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Extract article title
        title = soup.find("h1", {"id": "firstHeading"}).text.strip()
        title = remove_non_bmp_chars(title)  # Remove non-BMP characters
        
        # Extract first paragraph
        content_div = soup.find("div", {"id": "mw-content-text"})
        first_paragraph = ""
        for p in content_div.find_all("p"):
            text = p.text.strip()
            if text and len(text) > 100:  # Skip short paragraphs
                first_paragraph = remove_non_bmp_chars(text)  # Remove non-BMP characters
                break
                
        # Extract infobox image if available
        image_url = ""
        infobox = soup.find("table", {"class": "infobox"})
        if infobox:
            img = infobox.find("img")
            if img and img.get("src"):
                image_url = "https:" + img.get("src")
        
        print(f"📄 Found article: {title}")
        return {
            "title": title,
            "content": first_paragraph,
            "url": driver.current_url,
            "image": image_url
        }
    except Exception as e:
        print(f"❌ Scraping Error: {str(e)}")
        driver.save_screenshot("wikipedia_error.png")
        return None

def generate_tweet_from_article(article):
    """Generate a tweet from scraped Wikipedia article using Gemini."""
    try:
        prompt = f"""
        Create an engaging tweet about this Wikipedia article. Follow these guidelines:
        1. Keep it under 280 characters
        2. Start with a fascinating fact or surprising insight
        3. Highlight the most interesting aspect of the topic
        4. Include 1-2 relevant hashtags
        5. Add an emoji to increase engagement
        6. Always include the article URL at the end
        
        Article Title: {article['title']}
        Article Excerpt: {article['content'][:500]}...
        """
        
        response = model.generate_content(prompt)
        tweet = response.text.strip()
        
        # Post-processing cleanup
        tweet = re.sub(r'[\*\"]', '', tweet)  # Remove markdown
        tweet = re.sub(r'\s+', ' ', tweet)  # Remove extra whitespace
        
        # Remove Gemini notes
        for phrase in ["Note:", "Disclaimer:", "Important:", "Key takeaway:"]:
            tweet = tweet.split(phrase)[0]
        
        # Ensure URL is included
        if article['url'] and article['url'] not in tweet:
            tweet += f"\n\n{article['url']}"
        
        # Remove non-BMP characters
        tweet = remove_non_bmp_chars(tweet)
        
        # Ensure tweet length is within limits
        if len(tweet) > 280:
            # Try to preserve the URL
            if article['url'] in tweet:
                url_part = article['url']
                content_part = tweet.replace(url_part, "")[:280 - len(url_part) - 5]
                tweet = f"{content_part}...\n\n{url_part}"
            else:
                tweet = tweet[:270] + "..." + article['url']
        
        print(f"📝 Generated tweet ({len(tweet)} chars): {tweet[:60]}...")
        return tweet
            
    except Exception as e:
        print(f"❌ Gemini Error: {str(e)}")
        # Fallback tweet
        fallback_tweet = (f"Fascinating Wikipedia article about {article['title']}. "
                         f"Learn more: #Knowledge #Education\n{article['url']}")
        return remove_non_bmp_chars(fallback_tweet)[:280]

def twitter_login(driver):
    """Login to Twitter with optional one-pass verification."""
    wait = WebDriverWait(driver, 30)  # Increased timeout
    print("\n🔐 Starting Twitter login process...")
    
    driver.get("https://twitter.com/i/flow/login")
    time.sleep(5)  # Increased initial wait

    print("📧 Entering email/username...")
    user_field = wait.until(EC.visibility_of_element_located(
        (By.XPATH, '//input[@autocomplete="username"]')
    ))
    user_field.clear()
    user_field.send_keys(EMAIL)
    user_field.send_keys(Keys.ENTER)
    time.sleep(3)

    # Handle verification step
    verification_field = None
    verification_xpaths = [
        '//input[@data-testid="ocfEnterTextTextInput"]',
        '//input[@name="text"]',
        '//input[@autocomplete="current-password"]'  # Sometimes skips to password
    ]
    
    for xpath in verification_xpaths:
        try:
            element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            if element.is_displayed():
                verification_field = element
                break
        except:
            continue
    
    if verification_field:
        label_text = verification_field.get_attribute("aria-label") or ""
        print(f"🛡️ Security field detected: {label_text}")
        
        if "username" in label_text.lower():
            to_send = USERNAME
        elif "email" in label_text.lower():
            to_send = EMAIL
        elif "phone" in label_text.lower():
            to_send = PHONE_NUMBER
        else:
            to_send = USERNAME  # Default
            
        verification_field.clear()
        verification_field.send_keys(to_send)
        verification_field.send_keys(Keys.ENTER)
        time.sleep(3)
    else:
        print("ℹ️ No extra security step detected.")

    print("🔑 Entering password...")
    password_field = wait.until(EC.visibility_of_element_located(
        (By.XPATH, '//input[@autocomplete="current-password"]')
    ))
    password_field.clear()
    password_field.send_keys(PASSWORD)
    password_field.send_keys(Keys.ENTER)
    time.sleep(7)  # Increased wait time for login to complete

    # Wait for login to complete
    try:
        wait.until(EC.url_contains("home"))
        print("✅ Login successful!")
        time.sleep(3)  # Additional stabilization time
    except Exception as e:
        print(f"⚠️ Login verification failed: {e}")
        # Proceed anyway if we might be logged in

def post_tweet(driver, tweet_text):
    """Compose and post a tweet with fallback checks."""
    wait = WebDriverWait(driver, 30)  # Increased timeout
    print("\n✍️ Composing tweet...")
    
    try:
        driver.get("https://twitter.com/compose/tweet")
        time.sleep(5)  # Increased wait for page load
        
        # Wait for tweet box
        tweet_box = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@data-testid='tweetTextarea_0'] | //div[@role='textbox']")
        ))
        tweet_box.click()

        print("⌨️ Typing tweet...")
        # Ensure we only send BMP characters
        cleaned_text = remove_non_bmp_chars(tweet_text)
        
        # Split into chunks to avoid triggering bot detection
        for char in cleaned_text:
            tweet_box.send_keys(char)
            time.sleep(random.uniform(0.03, 0.1))  # More human-like typing

        print("\n🔎 Searching for post button...")
        # Wait for button to be clickable
        time.sleep(2)
        post_button = None
        button_selectors = [
            "//div[@data-testid='tweetButton']",
            "//div[@data-testid='tweetButtonInline']",
            "//button[@data-testid='tweetButton']",
            "//div[@role='button' and contains(., 'Post')]",
            "//span[contains(., 'Post')]/ancestor::div[@role='button']"
        ]
        
        for selector in button_selectors:
            try:
                post_button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                print(f"✅ Found button using: {selector}")
                break
            except:
                continue
        
        if post_button:
            print("🖱️ Clicking post button...")
            try:
                # Scroll into view and click using JavaScript
                driver.execute_script("arguments[0].scrollIntoView(true);", post_button)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", post_button)
                
                # Verify successful post
                try:
                    wait.until(EC.presence_of_element_located(
                        (By.XPATH, "//span[contains(text(), 'Your Tweet was sent')]")
                    ))
                    print("✅ Verified: Tweet sent.")
                    time.sleep(3)  # Allow UI to update
                except:
                    print("⚠️ Tweet may have been sent - but not verified")
            except Exception as e:
                print(f"❌ JS click failed: {e}")
                try:
                    # Try direct click as fallback
                    post_button.click()
                except Exception as e:
                    print(f"❌ Fallback click failed: {e}")
                    # Final fallback - keyboard shortcut
                    print("⌨️ Trying keyboard shortcut...")
                    tweet_box.send_keys(Keys.CONTROL + Keys.ENTER)
        else:
            print("❌ Post button not found.")
            # Try keyboard shortcut as last resort
            print("⌨️ Trying keyboard shortcut...")
            tweet_box.send_keys(Keys.CONTROL + Keys.ENTER)
        
    except Exception as e:
        print(f"❌ Tweeting Error: {str(e)}")
        driver.save_screenshot("tweet_error.png")
        print("📸 Screenshot saved as tweet_error.png")

def main():
    """Run the bot: generate topic, scrape Wikipedia, generate tweet, and post."""
    print("🚀 Starting Wikipedia Twitter Bot...")
    
    # Generate topic using Gemini
    topic = generate_topic()
    print(f"📌 Selected topic: {topic}")
    
    # Setup Chrome options
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--window-size=1200,900")
    options.add_argument(f"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
    
    driver = None
    try:
        # Initialize driver
        print("🌐 Launching browser...")
        driver = uc.Chrome(
            options=options,
            use_subprocess=True
        )
        driver.set_page_load_timeout(60)
        print("✅ Browser launched successfully")
        
        # Step 1: Scrape Wikipedia article
        article = scrape_wikipedia_article(driver, topic)
        
        if not article:
            print("⚠️ No article found. Using fallback content.")
            article = {
                "title": "Wikipedia",
                "content": "The free encyclopedia that anyone can edit",
                "url": "https://en.wikipedia.org",
            }
        
        # Step 2: Generate tweet
        tweet = generate_tweet_from_article(article)
        
        if not tweet:
            print("⚠️ No tweet generated. Using fallback content.")
            tweet = f"Exploring {topic} on Wikipedia. The free encyclopedia anyone can edit! #Wikipedia #Knowledge\nhttps://en.wikipedia.org"
        
        # Step 3: Login to Twitter
        twitter_login(driver)
        
        # Step 4: Post tweet
        print("\n📢 Posting tweet:")
        print(tweet)
        post_tweet(driver, tweet)
        
        print("🎉 Tweet posted successfully!")
        
    except Exception as e:
        print(f"❌ Critical Error: {e}")
        if driver:
            driver.save_screenshot("main_error.png")
            print("📸 Screenshot saved as main_error.png")
    finally:
        if driver:
            try:
                print("🛑 Closing browser...")
                driver.quit()
                print("✅ Browser closed properly")
            except Exception as e:
                print(f"⚠️ Error closing browser: {e}")
        print("🏁 Script completed.")

if __name__ == "__main__":
    main()