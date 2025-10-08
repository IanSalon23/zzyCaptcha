# zzyCaptcha (简体中文)

[Read this in English](README.md)

[![许可证](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

一个简单的、可自行部署的、基于“视觉暂留”效果的验证码服务。

本服务生成的动态GIF验证码易于人类识别，但对于机器人OCR识别则非常困难。它提供了一个安全的、以后端为中心的验证流程，使开发者可以轻松地将其集成到自己的网站中。

![zzyCaptcha 演示](https://i.imgur.com/TAHDdZB.gif) <!-- 占位符：请替换为真实的演示GIF图 -->

## 功能特性

- **安全设计**: 验证流程在服务器之间进行，绝不将密钥暴露于客户端。
- **轻量且独立**: 使用简单的 SQLite 文件数据库，无需部署额外的数据库服务。
- **易于集成**: 只需将验证码小部件放入您的表单，并在后端通过一次API调用即可完成验证。

## 技术栈

- **后端**: Python 3, Flask
- **图像生成**: Pillow, NumPy
- **数据库**: SQLite

## 安装与设置

1.  **克隆仓库:**
    ```bash
    git clone https://github.com/TianmuTNT/zzyCaptcha.git
    cd zzyCaptcha
    ```

2.  **创建并激活虚拟环境:**
    ```bash
    # Windows 系统
    python -m venv venv
    .\venv\Scripts\activate

    # macOS/Linux 系统
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **安装依赖:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **配置环境:**
    复制环境配置文件模板，并生成您的密钥。
    ```bash
    cp .env.example .env
    ```
    然后，打开 `.env` 文件并设置一个唯一的 `SECRET_KEY`。您可以使用 `python -c 'import secrets; print(secrets.token_hex(24))'` 命令来生成一个。


## 运行服务

- **开发环境:**
  ```bash
  python app.py
  ```
  服务将在 `http://0.0.0.0:5000` 上可用。

## 如何集成

将 zzyCaptcha 集成到您的网站主要包含两部分：

1.  **前端**: 将验证码小部件添加到您的表单中。
2.  **后端**: 通过一次服务器到服务器的API调用来验证用户的提交。

您可以参考 `templates/demo.html` 查看一个完整的示例。

### 前端设置

在您的页面中引入小部件的 CSS 和 JavaScript，并将小部件容器放置在您的表单内。

```html
<head>
    <!-- ... 其他 head 元素 ... -->
    <link rel="stylesheet" href="http://your-captcha-domain.com/static/captcha-widget.css">
</head>
<body>
    <form action="/your/form/handler" method="POST">
        <!-- ... 其他表单字段 ... -->

        <!-- zzyCaptcha 小部件 -->
        <div class="zzy-captcha-widget-container"></div>
        <input type="hidden" name="zzy_challenge_id" id="zzy_challenge_id">
        <input type="hidden" name="zzy_user_answer" id="zzy_user_answer">

        <button type="submit">Submit</button>
    </form>

    <script>
        window.zzyCaptchaConfig = {
            siteKey: "your_site_key", // 您 .env 文件中的 SITE_KEY
            selector: ".zzy-captcha-widget-container"
        };
    </script>
    <script src="http://your-captcha-domain.com/static/captcha.js"></script>
</body>
```

### 后端验证

当您的服务器收到表单提交时，它将包含 `zzy_challenge_id` 和 `zzy_user_answer` 字段。您的后端必须向 zzyCaptcha 服务的 `/api/verify` 端点发起一个 POST 请求。

**Python 示例:**

```python
import requests

ZZYCAPTCHA_SECRET_KEY = "your_zzycaptcha_secret_key" # 这是 .env 文件中的 SECRET_KEY
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
        # 验证码正确，继续处理表单逻辑
        print("用户是人类！")
        return True
    else:
        # 验证码错误
        print(f"验证失败: {verification_data.get('error')}")
        return False
```

## 许可证

本项目基于 Apache 2.0 许可证。详情请参阅 [LICENSE](LICENSE) 文件。
