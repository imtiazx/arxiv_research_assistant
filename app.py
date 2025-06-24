import streamlit as st
import requests
import os
import json
import pandas as pd
from datetime import datetime, timedelta
import re

# === Load .env variables ===
LANGFLOW_TOKEN = st.secrets["LANGFLOW_TOKEN"]

# === Langflow API Configuration ===
API_URL = "https://api.langflow.astra.datastax.com/lf/d2b3e98e-4aae-4715-8695-f50c9ae8cf50/api/v1/run/9aa1c11b-f102-42f5-8038-30fb504d4639"

def extract_structured_content(response_data):
    """Extract clean, structured content from API response"""
    try:
        # Navigate the deeply nested response to find the text content
        # Correct path: response['outputs'][0]['outputs'][0]['results']['message']['text']
        if 'outputs' in response_data and response_data['outputs']:
            first_output_list = response_data['outputs'][0].get('outputs', [])
            if first_output_list:
                first_result = first_output_list[0].get('results', {})
                message = first_result.get('message', {})
                
                # The text can be in 'text' or 'data.text'
                text_response = message.get('text')
                if not text_response and 'data' in message:
                    text_response = message['data'].get('text', '')

                if text_response:
                    # Clean up common JSON formatting issues
                    text_response = text_response.replace('\\n', '\n').replace('\\"', '"')
                    
                    # If it's a structured response, format it for better display
                    if any(marker in text_response for marker in ['**', '*', '•', '- ', 'Key findings:', 'Abstract:', 'Summary:']):
                        return format_structured_response(text_response)
                    else:
                        return text_response
        
        # Fallback if the structure is not as expected
        return str(response_data)
        
    except (KeyError, IndexError, TypeError) as e:
        return f"Error parsing response structure: {e}"

def format_structured_response(text):
    """Format structured responses for better readability"""
    # If it's a summary with bullet points, enhance the formatting
    if '**' in text and ('*' in text or '•' in text):
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append('')
                continue
                
            # Format headers
            if line.startswith('**') and line.endswith('**'):
                formatted_lines.append(f"### {line}")
            # Format bullet points
            elif line.startswith('*') and not line.startswith('**'):
                formatted_lines.append(f"- {line[1:].strip()}")
            elif line.startswith('•'):
                formatted_lines.append(f"- {line[1:].strip()}")
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    return text

def parse_paper_data(text_response):
    """Parse the response text and extract paper information, supporting both markdown and plain text field labels, and extracting the title from markdown links if present."""
    papers = []
    lines = text_response.split('\n')
    current_paper = {}

    # Patterns for different markdown title styles and plain text
    title_patterns = [
        re.compile(r'^\d+\.\s*\*\*Title\*\*:?\s*(.*)', re.IGNORECASE), # 1. **Title**: ...
        re.compile(r'^\d+\.\s*\*\*(.*?)\*\*'),   # **Title**
        re.compile(r'^\d+\.\s*__(.*?)__'),           # __Title__
        re.compile(r'^\d+\.\s*\*(.*?)\*'),         # *Title*
        re.compile(r'^\d+\.\s*(.*?)$'),              # fallback: numbered title
        re.compile(r'^Title:?[ \t]*(.+)', re.IGNORECASE), # Title: ... (must have at least one character after colon)
    ]

    def extract_markdown_link_text(s):
        # If s is in the form [text](url), return text, else return s
        m = re.match(r'\[(.*?)\]\([^\)]+\)', s)
        return m.group(1).strip() if m else s.strip()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Look for paper titles (various markdown styles and plain text)
        matched = False
        for pat in title_patterns:
            m = pat.match(line)
            if m:
                # Save previous paper if exists
                if current_paper:
                    papers.append(current_paper)
                title_val = m.group(1).strip() if m.group(1) else ''
                title_val = extract_markdown_link_text(title_val)
                current_paper = {
                    'title': title_val if title_val else 'Unknown Title',
                    'categories': '',
                    'url': '',
                    'summary': '',
                    'authors': '',
                    'published': ''
                }
                matched = True
                break
        if matched:
            continue

        # Look for authors (plain or markdown)
        authors_match = re.search(r'Authors?:?\s*(.*)', line, re.IGNORECASE)
        if authors_match and current_paper is not None:
            val = authors_match.group(1).strip().lstrip(':').lstrip('*').strip()
            current_paper['authors'] = val
            continue

        # Look for published date
        published_match = re.search(r'Published:?\s*([A-Za-z]+ \d{1,2}, \d{4})', line)
        if published_match and current_paper is not None:
            val = published_match.group(1).strip().lstrip(':').lstrip('*').strip()
            current_paper['published'] = val
            continue

        # Look for summary (plain or markdown)
        summary_match = re.search(r'(Summary|Abstract):?\s*(.*)', line, re.IGNORECASE)
        if summary_match and current_paper is not None:
            val = summary_match.group(2).strip().lstrip(':').lstrip('*').strip()
            current_paper['summary'] = val
            continue

        # Look for URLs (arxiv links)
        url_match = re.search(r'(https?://arxiv\.org/[\w\-/\.]+)', line)
        if url_match and current_paper is not None:
            current_paper['url'] = url_match.group(1)
            continue

    # Add the last paper
    if current_paper:
        papers.append(current_paper)

    return papers

def format_structured_paper_list(papers):
    """Format a list of papers in a structured, readable way with clear fields and dividers, each field on its own line and no stray asterisks."""
    if not papers:
        return "No papers found in the expected format."
    output = []
    for paper in papers:
        # Title as plain text with label, followed by a blank line
        title_val = paper.get('title', 'Unknown Title').strip(':').strip('*').strip()
        output.append(f"**Title:** {title_val}")
        output.append("")
        # Authors
        authors_val = paper.get('authors', '').strip(':').strip('*').strip()
        if authors_val:
            output.append(f"**Authors:** {authors_val}")
            output.append("")
        # Published date
        published_val = paper.get('published', '').strip(':').strip('*').strip()
        if published_val:
            output.append(f"**Published:** {published_val}")
            output.append("")
        # Summary
        summary_val = paper.get('summary', '').strip(':').strip('*').strip()
        if summary_val:
            output.append(f"**Summary:** {summary_val}")
            output.append("")
        # PDF Link
        url_val = paper.get('url', '').strip()
        if url_val:
            output.append(f"**PDF Link:** {url_val}")
            output.append("")
        # Divider
        output.append('---')
    return '\n'.join(output)

def format_paper_display(papers, max_papers=3):
    """Format papers for better display"""
    if not papers:
        return "No papers found in the expected format."
    
    formatted_output = f"## 📄 Found {min(len(papers), max_papers)} Recent Papers\n\n"
    
    for i, paper in enumerate(papers[:max_papers]):
        formatted_output += f"### {i+1}. {paper.get('title', 'Unknown Title')}\n"
        
        if paper.get('categories'):
            formatted_output += f"**Categories:** `{paper['categories']}`\n\n"
        
        if paper.get('url'):
            formatted_output += f"**Link:** [{paper['url']}]({paper['url']})\n\n"
        
        if paper.get('summary'):
            formatted_output += f"**Summary:** {paper['summary']}\n\n"
        
        formatted_output += "---\n\n"
    
    return formatted_output

def create_papers_dataframe(papers):
    """Create a DataFrame from papers data (Title as plain text, URL as arxiv link, no Categories column)"""
    if not papers:
        return None
    df_data = []
    for paper in papers:
        # If title is in markdown link format, extract only the text
        title = paper.get('title', 'Unknown')
        # Remove markdown link if present
        if title.startswith('[') and '](' in title and title.endswith(')'):
            title = title[1:title.index('](')]
        # If title is the literal word 'Title', skip or set as Unknown
        if title.strip().lower() == 'title':
            title = 'Unknown Title'
        df_data.append({
            'Title': title,
            'URL': paper.get('url', 'N/A')
        })
    return pd.DataFrame(df_data)

def is_paper_list_response(response_text):
    """Return True if the response looks like a paper list (at least 2 parsed papers or starts with numbered titles)."""
    papers = parse_paper_data(response_text)
    if len(papers) >= 2:
        return True
    # Also check if the response starts with a numbered list
    lines = response_text.strip().split('\n')
    numbered_lines = [line for line in lines if re.match(r'^\d+\. ', line)]
    return len(numbered_lines) >= 2

# === Function to call Langflow ===
def query_langflow(user_input, openai_api_key):
    """Query Langflow API"""
    
    payload = {
        "input_value": user_input,
        "output_type": "chat",
        "input_type": "chat",
        "tweaks": {
            "Agent-Ex18F": {
                "api_key": openai_api_key
            }
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LANGFLOW_TOKEN}"
    }

    # Debug: Show request details
    print(f"API URL: {API_URL}")
    print(f"Headers: {headers}")
    print(f"Payload: {payload}")

    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=120)
        
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        print(f"Raw Response: {response.text}")
        
        response.raise_for_status()
        
        response_data = response.json()
        
        # Debug: Show raw response
        print(f"Parsed Response Data: {response_data}")
        
        # Extract the structured content
        clean_response = extract_structured_content(response_data)
        print(f"Extracted Clean Response: {clean_response}")
        
        return clean_response
        
    except requests.exceptions.HTTPError as e:
        if response.status_code == 504:
            return "❌ Error: Gateway Timeout. The request took too long. Try a simpler query."
        elif response.status_code == 401:
            return "❌ Error: Authentication failed. Please check your LANGFLOW_TOKEN."
        elif response.status_code == 404:
            return "❌ Error: Flow not found. Please check your API URL."
        else:
            return f"❌ HTTP error {response.status_code}: {e}"
    except requests.exceptions.Timeout:
        return "❌ Error: The request timed out. Try a simpler query."
    except requests.exceptions.RequestException as e:
        return f"❌ Request error: {e}"
    except Exception as e:
        return f"❌ Unexpected error: {e}"

# === Streamlit UI ===
st.set_page_config(
    page_title="ArXiv Research Assistant", 
    page_icon="📚", 
    layout="wide"
)

st.title("📚 ArXiv Research Assistant")
st.markdown("*Powered by Langflow & GPT-4o-mini*")

# === Sidebar with instructions ===
with st.sidebar:
    st.header("🔑 Enter Your OpenAI API Key")
    openai_api_key = st.text_input("OpenAI API Key", type="password")
    st.markdown("**You must provide your own OpenAI API key to use this app.**")
    st.header("🔧 How to Use")
    st.markdown("""
    1. **Search for papers**: Ask about specific research topics
    2. **Ask follow-up questions**: The system remembers previous searches  
    3. **Get summaries**: Request summaries of found papers
    
    **Example Prompts:**
    - *"Find 3 papers on generative AI scaling approaches, published in 2025"*
    - *"Show me 2 recent papers on reinforcement learning from last year"*
    - *"Get 4 papers about machine learning optimization techniques within last 8 months"*
    
    **Follow-up Questions:**
    - *"Summarize the key findings from the first paper"*
    - *"What methodology did the second paper use?"*
    - *"Compare the approaches in these papers"*
    """)

# === Initialize session state ===
if "messages" not in st.session_state:
    st.session_state.messages = []

# === Display chat history ===
chat_container = st.container()

with chat_container:
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(message['content'])
        else:
            with st.chat_message("assistant"):
                content = message['content']
                if is_paper_list_response(content):
                    papers = parse_paper_data(content)
                    if papers:
                        st.markdown(format_structured_paper_list(papers))
                        df = create_papers_dataframe(papers)
                        if df is not None:
                            st.dataframe(df, use_container_width=True)
                    else:
                        st.markdown(content)
                else:
                    st.markdown(content)

# === Input section ===
st.markdown("---")

user_input = st.chat_input("Ask about research papers (be specific for better results)...")

if user_input and user_input.strip():
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
    with st.chat_message("assistant"):
        with st.spinner("🔍 Searching ArXiv and processing..."):
            response = query_langflow(user_input, openai_api_key)
        if is_paper_list_response(response):
            papers = parse_paper_data(response)
            if papers:
                st.markdown(format_structured_paper_list(papers))
                df = create_papers_dataframe(papers)
                if df is not None:
                    st.dataframe(df, use_container_width=True)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv,
                        file_name=f"arxiv_papers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            else:
                st.markdown(response)
        else:
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
