# X (Twitter) Automation Tool

A Python-based automation tool for X (formerly Twitter) using Playwright.

## ⚠️ Disclaimer

This tool is for educational purposes only. Please note:

- Using automation tools might violate X's Terms of Service
- Use at your own risk
- The authors are not responsible for any account suspensions or other consequences
- This is not an official X product

## 🚀 Features

- Automated login with email verification handling
- Post text tweets
- Post tweets with images (supports both URLs and local files)
- Persistent browser session

## 📋 Requirements

- Python 3.8+
- Playwright
- Requests

## 🛠️ Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/x-automation.git
cd x-automation
```

2. Create and activate virtual environment:

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
playwright install chromium
```

## 💻 Usage

Basic usage example:

```python
from x_automation import XAutomation

Initialize the bot
bot = XAutomation()
Login (use environment variables for credentials)
bot.login()
Post a simple text tweet
bot.post_tweet("Hello, World!")
Post a tweet with local image
bot.post_tweet_with_image(
text="Check out this image!",
image_path="path/to/local/image.jpg"
)
Post a tweet with image from URL
bot.post_tweet_with_image(
text="Check out this image!",
image_path="https://example.com/image.jpg"
)
```

## ⚙️ Configuration

1. Create a `.env` file in the project root:

```plaintext
X_USERNAME=your_username
X_EMAIL=your_email
X_PASSWORD=your_password
```

2. Never commit your `.env` file to version control!

## 🔒 Security Considerations

- Store credentials in environment variables
- Use a dedicated testing account
- Be mindful of X's rate limits
- Don't share your credentials or cookies
- Regularly update dependencies

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🐛 Known Issues

- X's interface may change, requiring selector updates
- Rate limiting may occur with frequent usage
- Some image types might not be supported
- Login flow might change requiring updates

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Legal Notice

This project is not affiliated with, authorized, maintained, sponsored or endorsed by X (Twitter) or any of its affiliates or subsidiaries. This is an independent and unofficial software. Use at your own risk.

## 📞 Support

- Create an issue for bug reports
- Start a discussion for feature requests
- Check existing issues before creating new ones
