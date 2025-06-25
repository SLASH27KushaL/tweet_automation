    # 🤖 Twitter Tech Tweet Automation Bot

This is a fully automated Python bot that logs into Twitter, generates tweets belonging to various categories using Google's **Gemini AI**, and posts it using **Selenium** with an **undetected Chrome driver**. It mimics human behavior and handles Twitter's one-pass security flow intelligently.

---

## 📦 Features

- 🔐 Auto Twitter login with dynamic verification (username/email/phone)
- 🧠 AI-generated tweets using Gemini (`gemini-1.5-flash`)
- ⌨️ Human-like typing for realism
- 🕵️ Robust debugging for UI interactions
- 📸 Screenshot capture on error

---

## 📁 File Structure

```
.
├── tweet_automation.py       # Main script
├── .env                      # Stores credentials and API keys
├── tweet_error.png           # Saved if tweet fails
├── main_error.png            # Saved if login or setup fails
└── README.md                 # You're reading it
```

---

## 🔧 Prerequisites

- Python 3.8+
- Chrome browser installed
- ChromeDriver auto-handled by `undetected-chromedriver`

---

## 📦 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/SLASH27KushaL/tweet_automation
cd tweet_automation
```

### 2. Install Dependencies

```bash
pip install python-dotenv undetected-chromedriver selenium google-generativeai
```

### 3. Set Up Environment Variables

Create a `.env` file in the root directory and add:

```env
TWITTER_EMAIL=youremail@example.com
TWITTER_USERNAME=yourhandle  # without '@'
TWITTER_PASSWORD=yourpassword
TWITTER_PHONE=yourphonenumber  # optional
GEMINI_API_KEY=your_gemini_api_key
```

---

## 🚀 Usage

Run the script using:

```bash
python tweet_automation.py
```

The script will:

- ✅ Generate a tweet using Gemini AI
- ✅ Open a stealth Chrome browser
- ✅ Log into your Twitter account
- ✅ Post the tweet

---

## 💡 Example Output

```
🚀 Twitter Auto-Poster Starting...
🧠 Generated Tweet:
Debugging is like being the detective in a crime movie where you are also the murderer.
🔐 Starting Twitter login process...
📧 Entering email/username...
🛡️ Security field detected: `username`
🔑 Entering password...
✅ Login successful!
✍️ Starting tweet composition...
⌨️ Typing tweet...
🔎 Searching for post button...
✅ Tweet posted successfully!
🛑 Script completed.
```

---

## 🛠 Troubleshooting

- **Login issues?** Double-check `.env` and inspect Twitter UI changes.
- **Tweet not posting?** Check `tweet_error.png` for a screenshot.
- **Gemini error?** Verify your API key and check quota.

---

## 📸 Error Screenshots

- `tweet_error.png`: Tweeting failure snapshot.
- `main_error.png`: Setup or login failure snapshot.

---

## ⚠️ Disclaimer

This bot is for **educational and personal use only**. Automating Twitter may violate their [Terms of Service](https://twitter.com/en/tos). Use responsibly.

---

## 🙏 Credits

- [Google Generative AI](https://ai.google.dev/)
- [Undetected-Chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver)
- [Selenium](https://www.selenium.dev/)

    
