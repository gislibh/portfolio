### Streamlit + Ollama

Streamlit + Ollama is a local, privacy-focused tool for ingesting and analyzing your financial data. Drop in any kind of financial data—PDF bills, XLSX bank statements, or similar formats—and get instant insights, interactive analytics, and an AI assistant to discuss your numbers.

## Features

- **Data Ingestion:**  
  Upload PDFs (for bills) and XLSX files (for bank statements). The tool parses your files and extracts key information such as dates, amounts, and transaction details.

- **Analytics & Insights:**  
  Get visual breakdowns of your spending:
  - Monthly and yearly spending summaries
  - Detailed creditor breakdowns
  - Projections for recurring bills over the next 12 months
  - Custom visualizations built with matplotlib and seaborn

- **AI Assistant:**  
  Chat with a built-in AI assistant that helps you understand your financial data and answer your spending questions—all running locally.

- **Privacy-First:**  
  All your data stays on your machine. No corporate servers or cloud storage means your financial information is always private.

## Roadmap

- **Enhanced AI Interaction:**  
  Integrate embeddings and vector databases so that the AI can intelligently interact with and reference your financial data.
  
- **Automate Data collection:**  
  Automate datacollection from specified accounts 
  
- **Expanded Data Sources:**  
  Support for more file formats and financial institutions.

## Getting Started

### Prerequisites

- Python 3.8 or higher  
- [Streamlit](https://streamlit.io/)  
- [Pandas](https://pandas.pydata.org/)
- [Ollama](https://ollama.com/)
- Other dependencies listed in `requirements.txt` (e.g., `openpyxl` for XLSX support)


### Installation

1. Clone this repository:
```bash
  git clone git@github.com:gislibh/portfolio.git
  cd Streamlit + Ollama
```

2. (Optional) Create and activate a virtual environment:
```bash
  python -m venv venv
  source venv/bin/activate  # on Linux/Mac
  venv\Scripts\activate  # on Windows
```

3. Install the required dependencies:
```bash
  pip install -r requirements.txt
```

4. Install Ollama, use default port 11434
```bash
  ollama pull gemma3:12b
```

### Running the App

Start the Streamlit application:
```bash
  streamlit run app.py
```

Please use the TEST_DATA file for testing.