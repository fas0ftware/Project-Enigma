# 🧩 Project Enigma

**Powered by Aesthesius**

Project Enigma is a sleek, Python-based QR Code Generator featuring a modern aesthetic interface. It allows users to quickly input data, generate QR codes, and save them in high quality.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-yellow.svg)

## 🌟 Features

* **Modern UI:** Powered by `CustomTkinter`, fully supporting Dark Mode.
* **Instant Generation:** Generates high-resolution QR codes instantly from text or links.
* **Easy Save:** Save your generated QR codes as `.png` files with a single click.
* **Error Handling:** User-friendly validation and error messages.

## 🛠️ Installation

Follow these steps to run the project on your local machine.

### Requirements

* Python 3.x
* pip

### Step-by-Step Setup

1.  **Clone the repository (or download):**
    ```bash
    git clone https://github.com/fas0ftware/project-enigma.git
    cd project-enigma
    ```

2.  **Create and activate a Virtual Environment (venv):**
    * *Windows:*
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```
    * *macOS/Linux:*
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## 🚀 Usage

After installation, run the application using:

```bash
python main.py

Enter the link or text you want to convert into the input field.

Click the "Generate QR" button.

Once the preview appears, click "Save Image" to download the file.
```

## 📂 Tech Stack
```bash
Language: Python

GUI: CustomTkinter

Image Processing: Pillow (PIL)

QR Engine: qrcode
```

## 👤 Author
Anıl (Aesthesius) Coding the future.