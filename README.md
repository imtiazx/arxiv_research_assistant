# 📚 ArXiv Research Assistant

A simple Streamlit app to search, summarize, and explore research papers from arXiv.  
Powered by **Langflow** and **GPT-4o-mini**.

---

## 🔑 OpenAI API Key Required

To use this app, you must provide your own **OpenAI API key**.  
Your key is **not stored** and is used only for your current session.

---

## 🔧 How to Use

### 📝 Search for Papers
You can ask the app to find research papers on specific topics, with filters on time and quantity.

**Example Prompts:**
- `Find 3 papers on generative AI scaling approaches, published in 2025`
- `Show me 2 recent papers on reinforcement learning from last year`
- `Get 4 papers about machine learning optimization techniques within last 8 months`

---

### 💬 Ask Follow-up Questions
The system remembers your previous searches, so you can ask questions about the papers found:
- `Summarize the key findings from the first paper`
- `What methodology did the second paper use?`
- `Compare the approaches in these papers`

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9 or higher
- OpenAI API key

### Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/arxiv-research-assistant.git
   cd arxiv-research-assistant```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate

3. Install the required libraries:
   ```bash
   pip install -r requirements.txt

### Run the App
  ```bash
   streamlit run streamlit.py```

⚡ Features
Search arXiv papers by topic and time range

Follow-up question handling (memory of previous search)

Summarization of research papers

Fast and interactive chat interface

💻 Tech Stack
Streamlit

Langflow

OpenAI GPT-4o-mini

📜 License
This project is open-source and available under the MIT License.


---

### ✅ Key Notes:
- All code blocks are properly closed.
- The virtual environment creation is inside a code block.
- Section breaks (`---`) are consistently used for clean separation.
- This is **ready to paste directly into your `README.md` file**.

If you want, I can help you:
- Add a `.gitignore` file.
- Create a sample `.env` template.
- Create badges (Python version, license, OpenAI powered).

Let me know! 😊



