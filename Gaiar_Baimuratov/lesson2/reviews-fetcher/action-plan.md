# App Review Feature Request Analysis - Action Plan

This step-by-step checklist is designed for implementing the feature request analysis pipeline. The checklist includes project setup, linting/formatting, and unit testing practices.

---

**Project: App Review Feature Request Analysis**

**Goal:** Analyze Appbot reviews using LLMs to extract, group, and format feature requests with corresponding user interview questions into a final JSON output.

**Checklist:**

**Phase 0: Project Setup & Configuration**

* [ ] **1. Create Project Directory:**
    * Create a new directory for the project (e.g., `app_review_analyzer`).
    * Navigate into the new directory.
* [ ] **2. Initialize Git Repository:**
    * Run `git init` to initialize a Git repository for version control.
* [ ] **3. Set Up Virtual Environment:**
    * Create a Python virtual environment: `python -m venv venv`
    * Activate the virtual environment (e.g., `source venv/bin/activate` on Linux/macOS, `venv\Scripts\activate` on Windows).
* [ ] **4. Install Core Dependencies:**
    * Install necessary Python libraries:
        * `pip install requests` (if no specific Appbot wrapper is used)
        * `pip install openai` (for GPT-4o)
        * `pip install python-dotenv` (for managing API keys)
        * *(Optional but recommended)* `pip install tiktoken` (for accurate token counting for chunking)
        * *(Identify and install specific Appbot Python wrapper if available)* Check Appbot documentation for an official or community Python wrapper. If found, install it via pip. If not, plan to use the `requests` library directly.
* [ ] **5. Install Development Dependencies (Linting, Formatting, Testing):**
    * Install tools for code quality and testing:
        * `pip install pytest pytest-mock` (for unit testing and mocking)
        * `pip install black` (for code formatting)
        * `pip install flake8` (for code linting) or `pip install ruff` (modern alternative combining linting/formatting)
* [ ] **6. Configure Linter/Formatter:**
    * Create configuration files if needed (e.g., `pyproject.toml` for Black/Ruff, `.flake8` for Flake8). Set basic rules.
    * *Action:* Run formatter (e.g., `black .`) and linter (e.g., `flake8 .` or `ruff check .`) to ensure setup is working. Fix any initial warnings.
* [ ] **7. Configure API Keys:**
    * Create a `.env` file in the project root.
    * Add your API keys to the `.env` file:
        ```
        APPBOT_API_KEY='YOUR_APPBOT_API_KEY'
        OPENAI_API_KEY='YOUR_OPENAI_API_KEY'
        # Add Appbot App ID if static
        APPBOT_APP_ID='YOUR_APP_ID'
        ```
    * Create a `.gitignore` file and add `.env`, `venv/`, `__pycache__/`, `*.pyc` to it.
    * Write a utility function (e.g., in `config.py`) to load these environment variables using `dotenv`.
* [ ] **8. Set Up Test Directory Structure:**
    * Create a `tests/` directory in the project root.
    * Create an empty `tests/__init__.py` file.

**Phase 1: Data Acquisition (Appbot Reviews)**

* [ ] **9. Implement Appbot API Wrapper/Client:**
    * Create a new Python file (e.g., `appbot_client.py`).
    * Define a function `Workspace_reviews(app_id: str, days: int = 365) -> list[str]`.
    * Inside the function:
        * Load the `APPBOT_API_KEY` and `app_id` (or pass `app_id` as an argument).
        * Consult the Appbot API documentation (or the wrapper's documentation). Determine the correct endpoint and parameters to fetch reviews for the specified `app_id`.
        * Crucially, identify how to fetch reviews for *all markets/countries* the app is available in. This might require multiple API calls or a specific parameter.
        * Set the time period to the last `days` (365).
        * Handle API authentication using the key.
        * Make the API request(s) using the chosen wrapper or `requests`.
        * Handle potential pagination in the API response to retrieve *all* reviews for the period.
        * Parse the responses and extract only the review text content.
        * Implement basic error handling (e.g., for network issues, invalid API key, rate limits).
        * Return a list of review text strings.
* [ ] **10. Write & Run Unit Tests for `Workspace_reviews`:**
    * Create a test file (e.g., `tests/test_appbot_client.py`).
    * Use `pytest` and `pytest-mock` (or `unittest.mock`) to mock the Appbot API calls.
    * Test scenarios: successful fetch, handling pagination, API error response, empty response, fetching across multiple markets (simulate based on assumed API behavior).
    * *Action:* Run `pytest`. Ensure all tests pass.
    * *Action:* Run linter/formatter on the new code. Fix issues.

**Phase 2: Data Preparation (Chunking)**

* [ ] **11. Implement Review Chunking:**
    * Create a new Python file (e.g., `review_processor.py`).
    * Define a function `chunk_reviews(reviews: list[str], max_tokens: int) -> list[list[str]]` (or `list[str]` if concatenating chunks).
    * Inside the function:
        * Use the `tiktoken` library to count tokens accurately for the target model (GPT-4o). Get the appropriate encoding (e.g., `tiktoken.encoding_for_model("gpt-4o")`).
        * Iterate through the list of reviews.
        * Group reviews into chunks. Ensure the total token count of the reviews in a chunk (plus estimated tokens for the prompt/overhead) stays below `max_tokens`. *Note: GPT-4o has a large context window, but chunking is still good practice.*
        * Return a list of chunks, where each chunk is a list of review strings (or one large concatenated string).
* [ ] **12. Write & Run Unit Tests for `chunk_reviews`:**
    * Create a test file (e.g., `tests/test_review_processor.py`).
    * Use `pytest`.
    * Test scenarios: empty review list, list smaller than `max_tokens`, list requiring multiple chunks, reviews with varying token counts.
    * *Action:* Run `pytest`. Ensure all tests pass.
    * *Action:* Run linter/formatter on the new code. Fix issues.

**Phase 3: Feature Extraction (GPT-4o)**

* [ ] **13. Implement Feature Extraction from Chunk:**
    * In `review_processor.py`, define a function `extract_features_from_chunk(chunk: list[str] | str, openai_client) -> list[str]`.
    * Inside the function:
        * Load the `OPENAI_API_KEY` and initialize the `openai` client.
        * Craft a clear and specific prompt for GPT-4o. The prompt should instruct the model to:
            * Read the provided review(s) in the `chunk`.
            * Identify and extract *explicit feature requests* mentioned by users. Ignore general complaints or praises unless they contain a specific request.
            * Output *only* a list of the identified feature request strings, one per line, or as a JSON list.
        * Format the input for the OpenAI API call (Chat Completions endpoint). Combine the prompt and the `chunk`.
        * Call the OpenAI API using the `openai` Python SDK, specifying the `gpt-4o` model.
        * Parse the response from GPT-4o to extract the list of feature requests.
        * Implement error handling for the API call (e.g., rate limits, content filtering).
        * Return the list of extracted feature request strings for this chunk.
* [ ] **14. Write & Run Unit Tests for `extract_features_from_chunk`:**
    * In `tests/test_review_processor.py`, add tests for the new function.
    * Use `pytest-mock` to mock the `openai.ChatCompletion.create` (or equivalent) call.
    * Test scenarios: chunk with no feature requests, chunk with one, chunk with multiple, chunk with ambiguous text. Verify parsing of mocked LLM responses.
    * *Action:* Run `pytest`. Ensure all tests pass.
    * *Action:* Run linter/formatter on the new code. Fix issues.

**Phase 4: Aggregation and Refinement**

* [ ] **15. Process All Chunks and Aggregate Requests:**
    * Create a main script (e.g., `main.py`).
    * Implement the main workflow:
        * Load necessary configurations (API keys, App ID).
        * Call `Workspace_reviews` to get all reviews.
        * Call `chunk_reviews` to break reviews into manageable chunks.
        * Initialize an empty list `all_raw_feature_requests`.
        * Initialize the OpenAI client.
        * Loop through each `chunk`:
            * Call `extract_features_from_chunk` for the current chunk.
            * Append the returned feature requests to `all_raw_feature_requests`.
            * *(Consider temporary storage)* For very large datasets, optionally write extracted features to a temporary file after processing each chunk to avoid memory issues and allow resuming.
* [ ] **16. Implement Feature Grouping and Refinement:**
    * In `review_processor.py`, define a function `group_and_refine_features(raw_feature_requests: list[str], openai_client) -> list[str]`.
    * Inside the function:
        * Craft a prompt for GPT-4o. Instruct the model to:
            * Take the `raw_feature_requests` list as input.
            * Analyze the list to identify similar or duplicate requests.
            * Group similar requests together.
            * For each group, synthesize a single, concise, and clear feature description representing the core request (this will become the "topic").
            * Output *only* a list of these unique, refined feature descriptions (topics), one per line or as a JSON list.
        * Call the OpenAI API (`gpt-4o` model) with the prompt and the raw feature list. *Note: Ensure the combined list doesn't exceed the context window; if it does, this step might need chunking itself or a different approach.*
        * Parse the response to get the list of refined feature topics.
        * Implement error handling.
        * Return the list of unique feature topics.
* [ ] **17. Write & Run Unit Tests for `group_and_refine_features`:**
    * In `tests/test_review_processor.py`, add tests for this function.
    * Use `pytest-mock` to mock the OpenAI API call.
    * Test scenarios: list with duplicates, list with similar but differently worded requests, list with unique requests, empty list. Verify the grouping/refinement based on mocked LLM output.
    * *Action:* Run `pytest`. Ensure all tests pass.
    * *Action:* Run linter/formatter on the new code. Fix issues.

**Phase 5: Interview Question Generation (GPT-4o)**

* [ ] **18. Implement Interview Question Generation:**
    * In `review_processor.py`, define a function `generate_interview_questions(feature_topic: str, openai_client) -> list[str]`.
    * Inside the function:
        * Craft a prompt for GPT-4o. Instruct the model to:
            * Receive a `feature_topic` as input.
            * Generate exactly 3 insightful "core questions" about this feature topic.
            * These questions should be suitable for a user interview session led by a facilitator.
            * Questions should aim to understand: initial reaction, potential use cases/value, and any concerns (as demonstrated in the example format).
            * Output *only* the 3 questions, preferably as a JSON list of strings.
        * Call the OpenAI API (`gpt-4o` model) with the prompt and the feature topic.
        * Parse the response to get the list of 3 questions.
        * Implement error handling. If the response doesn't contain exactly 3 questions, handle gracefully (e.g., log a warning, return default questions, retry).
        * Return the list of questions.
* [ ] **19. Write & Run Unit Tests for `generate_interview_questions`:**
    * In `tests/test_review_processor.py`, add tests for this function.
    * Use `pytest-mock` to mock the OpenAI API call.
    * Test scenarios: typical feature topic, ensure exactly 3 questions are requested/parsed from the mocked response, handle potential error cases (e.g., malformed response from mock).
    * *Action:* Run `pytest`. Ensure all tests pass.
    * *Action:* Run linter/formatter on the new code. Fix issues.

**Phase 6: Final Output Generation**

* [ ] **20. Assemble Final JSON Output:**
    * In `main.py`, after getting the list of refined feature topics:
        * Initialize an empty list `final_output_data`.
        * Loop through each `refined_topic` in the list generated by `group_and_refine_features`.
        * For each `refined_topic`:
            * Call `generate_interview_questions(refined_topic, openai_client)` to get the questions.
            * Create a dictionary matching the required structure:
                ```python
                feature_entry = {
                  "topic": refined_topic,
                  "core_questions": generated_questions, # List of 3 strings
                  "max_followups": 3 # Constant value as specified
                }
                ```
            * Append `feature_entry` to the `final_output_data` list.
* [ ] **21. Write JSON to File:**
    * In `main.py`, after compiling the `final_output_data` list:
        * Use the `json` library to dump the list into a JSON formatted string: `json_output = json.dumps(final_output_data, indent=2)` (use `indent` for readability).
        * Write the `json_output` string to a file (e.g., `feature_requests_interview_plan.json`).
        * Add basic logging to indicate success or failure.
* [ ] **22. Write & Run Integration Tests (Optional but Recommended):**
    * Create an integration test file (e.g., `tests/test_main_integration.py`).
    * Mock the external services (`Appbot`, `OpenAI`) at a higher level.
    * Test the complete flow from dummy input reviews to the final JSON structure output.
    * *Action:* Run `pytest`. Ensure all tests pass.
    * *Action:* Run linter/formatter on all project code. Fix issues.

**Phase 7: Documentation and Finalization**

* [ ] **23. Add Docstrings and Type Hinting:**
    * Review all functions and add clear docstrings explaining their purpose, arguments, and return values.
    * Ensure type hints are used consistently throughout the code.
* [ ] **24. Create README File:**
    * Write a `README.md` file explaining:
        * What the project does.
        * How to set it up (install dependencies, set up `.env`).
        * How to run the main script.
        * How to run tests.
        * Any important configuration details.
* [ ] **25. Final Code Review & Commit:**
    * Read through the entire codebase one last time.
    * Ensure all checklist items are complete.
    * Make sure API keys are not committed (`.env` is in `.gitignore`).
    * Commit the final version to Git.
    
**Phase 8: Multi-Market Analysis**

* [ ] **26. Create Scripts for Multi-Market Analysis:**
    * Implement `pull_all_markets.py` to gather reviews from all available markets.
    * Implement `analyze_all_markets.py` to process reviews from multiple markets.
    * Add unit tests for multi-market analysis scripts.

**Phase 9: Data Management**

* [ ] **27. Create Data Management Tools:**
    * Implement cleanup utility script for data management.
    * Add options for dry run and keeping recent files.
    * Implement progress visualization for cleanup operations.
    * Ensure all code follows project quality standards.
    * Add unit tests for data management tools.

