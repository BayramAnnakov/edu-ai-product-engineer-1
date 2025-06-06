# Voice Data Agent

This project contains a voice-activated data analysis and visualization agent.

## Description

The agent is designed to interact with users via voice commands to:
- Load and preview CSV data.
- Answer questions about the data.
- Perform data analysis 
- Generate visualizations from the data.

## Structure

- `agent.py`: Main voice agent logic.
- `tools/`: Contains data utility functions like `read_csv` and `generate_plot`.
- `data/`: Likely intended for storing data files (e.g., `UberDataset.csv` is referenced).
- `visualizations/`: Likely intended for storing generated plots.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd voice_data_agent
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure necessary environment variables or API keys** (e.g., for Google AI services if `google.genai` is used for API calls).
