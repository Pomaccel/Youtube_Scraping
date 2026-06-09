# YouTube Scraping & Mini Analytics Dashboard 🚀

An interactive, web-based dashboard built with **Streamlit** that utilizes the official **Google YouTube Data API v3** to scrape, analyze, and export YouTube data (videos, channels, and comments) in real-time.

---

## 📌 Features

* **Interactive UI:** A clean, user-friendly dashboard powered by Streamlit.
* **Data Extraction:** Fetch deep insights from YouTube channels, specific videos, or comment sections.
* **Smart Exception Handling:** Robust logging and robust error handling via Google's `HttpError`.
* **Dynamic Exporting:** Download scraped data instantly as **CSV** or **JSON** directly from the browser (powered by `io` memory buffers).
* **Type-Safe & Clean:** Written using Python typing hints (`Optional`) for reliability and maintainability.

---

## 🛠️ Tech Stack & Dependencies

This project relies on the following core Python libraries:

* **Frontend Dashboard:** `streamlit`
* **Data API:** `google-api-python-client` (YouTube Data API v3)
* **Data Processing:** `pandas`
* **Utilities:** `re` (regex patterns), `time` & `datetime` (timestamps), `logging` (error tracking), `io` (in-memory file buffers).

---

## 🚀 Getting Started

### 1. Prerequisites
You will need a YouTube Data API Key. 
> 💡 [Get a Google API Key here](https://console.cloud.google.com/)

### 2. Installation
Clone the repository and install the dependencies:

```bash
# Clone the repository
git clone [https://github.com/Pomaccel/Youtube_Scraping.git](https://github.com/Pomaccel/Youtube_Scraping.git)

# Navigate into the project directory
cd Youtube_Scraping

# Install dependencies
pip install -r requirements.txt
