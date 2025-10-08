# zzyCaptcha

[Read this in Chinese (简体中文)](README.zh-CN.md)

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

A simple, self-hostable, "persistence of vision" CAPTCHA service.

This service generates animated GIF CAPTCHAs that are easy for humans to solve but difficult for bots to OCR. It provides a secure, backend-focused verification flow that is easy for developers to integrate into their websites.

![zzyCaptcha Demo](https://i.imgur.com/TAHDdZB.gif) <!-- Placeholder: Replace with an actual demo GIF -->

## Features

- **Secure by Design**: Verification is handled server-to-server, never exposing secret keys to the client.
- **Lightweight & Self-Contained**: Uses a simple SQLite database, requiring no external database servers.
- **Easy to Integrate**: Drop the widget into your form and verify submissions on your backend with a single API call.

## Tech Stack

- **Backend**: Python 3, Flask
- **Image Generation**: Pillow, NumPy
- **Database**: SQLite

## Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/TianmuTNT/zzyCaptcha.git
    cd zzyCaptcha
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # For Windows
    python -m venv venv
    .\venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure the environment:**
    Copy the example environment file and generate a secret key.
    ```bash
    cp .env.example .env
    ```
    Now, open the `.env` file and set a unique `SECRET_KEY`. You can generate one with `python -c 'import secrets; print(secrets.token_hex(24))'`.


## Running the Service

- **For Development:**
  ```bash
  python app.py
  ```
  The service will be available at `http://0.0.0.0:5000`.

## How to Integrate

Integrating zzyCaptcha into your website involves two parts:

1.  **Frontend**: Add the CAPTCHA widget to your form.
2.  **Backend**: Verify the user's submission by making a server-to-server call to the zzyCaptcha service.

See `templates/demo.html` for a complete example.

### Frontend Setup

Include the widget's CSS and JavaScript on your page, and place the widget container inside your form.

```html
<head>
    <!-- ... other head elements ... -->
    <link rel="stylesheet" href="http://your-captcha-domain.com/static/captcha-widget.css">
</head>
<body>
    <form action="/your/form/handler" method="POST">
        <!-- ... other form fields ... -->

        <!-- zzyCaptcha Widget -->
        <div class="zzy-captcha-widget-container"></div>
        <input type="hidden" name="zzy_challenge_id" id="zzy_challenge_id">
        <input type="hidden" name="zzy_user_answer" id="zzy_user_answer">

        <button type="submit">Submit</button>
    </form>

    <script>
        window.zzyCaptchaConfig = {
            siteKey: "your_site_key", // The SITE_KEY from your .env file
            selector: ".zzy-captcha-widget-container"
        };
    </script>
    <script src="http://your-captcha-domain.com/static/captcha.js"></script>
</body>
```

### Backend Verification

When your server receives the form submission, it will contain the `zzy_challenge_id` and `zzy_user_answer` fields. Your backend must then make a POST request to the zzyCaptcha `/api/verify` endpoint.

**Example in Python:**

```python
import requests

ZZYCAPTCHA_SECRET_KEY = "your_zzycaptcha_secret_key" # This is the SECRET_KEY from the .env file
ZZYCAPTCHA_VERIFY_URL = "http://your-captcha-domain.com/api/verify"

def handle_my_form_submission(form_data):
    challenge_id = form_data.get('zzy_challenge_id')
    user_answer = form_data.get('zzy_user_answer')

    response = requests.post(
        ZZYCAPTCHA_VERIFY_URL,
        json={
            'secret_key': ZZYCAPTCHA_SECRET_KEY,
            'challenge_id': challenge_id,
            'user_answer': user_answer
        }
    )

    verification_data = response.json()

    if verification_data.get('success'):
        # CAPTCHA was correct, proceed with form logic
        print("User is human!")
        return True
    else:
        # CAPTCHA was incorrect
        print(f"Verification failed: {verification_data.get('error')}")
        return False
```

## License

This project is licensed under the Apache 2.0 License. See the [LICENSE](LICENSE) file for details.
