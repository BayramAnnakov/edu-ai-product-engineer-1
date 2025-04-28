# Spotify User Board Simulation 👥🎙️

## 🚀 Overview

This project simulates a user feedback board meeting using AI agents. It processes real Spotify user reviews, clusters them to identify key themes and pain points, generates diverse user personas based on these clusters, and then simulates a discussion where these personas (represented by LLM agents) provide feedback on proposed product features.

The primary goal is to automate the process of gathering qualitative user insights and simulating user reactions to potential product changes in a structured and reproducible manner.

## 📂 Project Structure

```
.
├── Vladimir_Kovtunovskiy/homework2-userboard-simulation/
│   ├── cluster_outputs/          # Output directory for review clustering results
│   │   └── clusters_data.json    # JSON file containing clustered review data and keywords
│   ├── multiagent_outputs/       # Output directory for the user board simulation
│   │   ├── board_session.log     # Detailed log file for the simulation run
│   │   └── userboard_report.md   # Final markdown report summarizing the simulation
│   ├── data_types.py             # Defines shared data structures (Persona, FeatureProposal)
│   ├── persona_generator.py      # Generates user personas from cluster data using an LLM
│   ├── review_prep_pipeline.py   # Processes, cleans, embeds, and clusters user reviews
│   ├── board_simulation.py       # Core logic for simulating the multi-agent discussion
│   ├── userboard_pipeline.py     # Main script orchestrating the entire pipeline (clustering -> personas -> simulation)
│   ├── requirements.txt          # Python package dependencies
│   ├── spotify_reviews.csv       # Input dataset of Spotify user reviews
│   └── README.md                 # This file
└── ... (other project files/folders)
```

## 📄 File Descriptions

*   `spotify_reviews.csv`: The raw input data containing user reviews for Spotify.
*   `requirements.txt`: Lists the necessary Python libraries required to run the project.
*   `data_types.py`: Contains Python `dataclass` definitions for `Persona` and `FeatureProposal`, ensuring consistent data handling across modules.
*   `review_prep_pipeline.py`:
    *   Loads reviews from `spotify_reviews.csv`.
    *   Cleans and preprocesses the review text.
    *   Calculates sentiment scores (positive, neutral, negative).
    *   Generates text embeddings using Sentence Transformers (optimized for MPS).
    *   Performs dimensionality reduction using UMAP.
    *   Clusters the reviews using K-Means, determining the optimal 'k'.
    *   Extracts relevant keywords for each cluster using TF-IDF.
    *   Saves the clustering results, including keywords and sample reviews, to `cluster_outputs/clusters_data.json`.
*   `persona_generator.py`:
    *   Reads the `clusters_data.json` file.
    *   Uses an LLM (e.g., GPT-4) to generate distinct user `Persona` objects based on the characteristics and feedback within selected clusters.
*   `board_simulation.py`:
    *   Takes generated `Persona` objects and proposed `FeatureProposal`s as input.
    *   Initializes AI agents for each persona and a facilitator agent using LangChain/LangGraph.
    *   Simulates a structured discussion over several rounds, where the facilitator asks questions about the features and personas respond based on their profiles.
    *   Captures the entire discussion transcript.
*   `userboard_pipeline.py`:
    *   Acts as the main entry point and orchestrator.
    *   Sequentially runs the review preparation (if `clusters_data.json` doesn't exist or needs updating, though currently relies on pre-existing file), persona generation, feature ideation (based on clusters), and board simulation steps.
    *   Uses LangGraph to manage the state and flow between these steps.
    *   Generates a final summary report (`userboard_report.md`) in the `multiagent_outputs` directory.
*   `cluster_outputs/`: Directory where the output of `review_prep_pipeline.py` is stored.
*   `multiagent_outputs/`: Directory where the outputs of the `userboard_pipeline.py` (logs and the final report) are stored.

## ⚙️ Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd <your-repo-directory>/Vladimir_Kovtunovskiy/homework2-userboard-simulation
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
4.  **Download NLTK data (if not already present):**
    Run Python and execute:
    ```python
    import nltk
    nltk.download('vader_lexicon')
    nltk.download('stopwords')
    ```
5.  **Set up OpenAI API Key:**
    Create a `.env` file in the `Vladimir_Kovtunovskiy/homework2-userboard-simulation` directory and add your OpenAI API key:
    ```
    OPENAI_API_KEY='your_openai_api_key_here'
    ```
    Alternatively, set it as an environment variable.

## ▶️ Usage

The main pipeline can be executed by running the `userboard_pipeline.py` script:

```bash
python Vladimir_Kovtunovskiy/homework2-userboard-simulation/userboard_pipeline.py
```

This script will:

1.  Load cluster data from `cluster_outputs/clusters_data.json`. (Note: It assumes this file exists. You might need to run `review_prep_pipeline.py` separately first if it doesn't, although the pipeline currently doesn't automatically trigger it).
    ```bash
    # To generate cluster data (if needed):
    python Vladimir_Kovtunovskiy/homework2-userboard-simulation/review_prep_pipeline.py
    ```
2.  Select top clusters based on negative sentiment.
3.  Generate feature ideas based on selected clusters using an LLM.
4.  Generate user personas based on selected clusters using an LLM.
5.  Run the board simulation with the generated personas and features.
6.  Generate a summary report (`userboard_report.md`) and log file (`board_session.log`) in the `multiagent_outputs` directory.

### Individual Scripts

You can also run the `review_prep_pipeline.py` script independently if you only need to perform the review clustering:

```bash
# Uses default input ./spotify_reviews.csv and output ./cluster_outputs/
python Vladimir_Kovtunovskiy/homework2-userboard-simulation/review_prep_pipeline.py

# Specify input/output
python Vladimir_Kovtunovskiy/homework2-userboard-simulation/review_prep_pipeline.py --csv path/to/reviews.csv --out path/to/output_dir
```

## ✨ Key Features

*   **AI Agent Simulation:** Leverages LLMs to simulate realistic user personas and discussions.
*   **Data-Driven Personas:** Personas are grounded in real user feedback clusters.
*   **Automated Insight Generation:** Streamlines the process of understanding user sentiment and potential feature reception.
*   **Modular Pipeline:** Code is organized into distinct, reusable modules.
*   **MPS Acceleration:** Utilizes Apple Silicon GPUs for faster embedding generation in the clustering pipeline.
*   **LangGraph Orchestration:** Uses LangGraph for managing the multi-step simulation pipeline state.