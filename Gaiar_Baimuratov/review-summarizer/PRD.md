# AI Review Summarization Agents – Product Requirements Document

## Overview and Objectives

This document outlines the requirements for a Python 3.10 application that uses **CrewAI**, a multi-agent AI framework, to analyze mobile app reviews. The goal is to combine a **deterministic extractive summarizer** (NLP-based) with a **probabilistic abstractive summarizer** (LLM-based), then use a third agent to compare their outputs. By leveraging CrewAI’s ability to orchestrate specialized AI agents in a team ([Introduction - CrewAI](https://docs.crewai.com/introduction#:~:text=CrewAI%20is%20a%20lean%2C%20lightning,LangChain%20or%20other%20agent%20frameworks)), the system will produce concise summaries of app store reviews and evaluate the results for quality. 

**Scope:** The input data will initially be text-only app reviews fetched via the AppBot API. The design will remain **extensible** for multi-modal inputs (e.g. screenshots or audio in reviews) in the future. This means the architecture should accommodate adding agents/tools for image or audio processing down the line without significant rework. The PRD covers integration points, functional requirements for each agent, and an implementation plan with a checklist for development tasks.

## Key Components and Functional Requirements

### 1. AppBot API Integration (Review Extraction)

- **Description:** Integrate with the AppBot REST API to retrieve app review data programmatically. The system should connect to AppBot using an API key and secret, then fetch recent reviews for a specified app (e.g., by App ID).
- **Data Retrieval:** Use HTTPS requests with HTTP Basic Auth (API username and password) as per AppBot’s v2 API. For example, a GET request to the endpoint `/api/v2/apps/{app_id}/reviews` with the proper auth returns a JSON payload of reviews.
- **Data Contents:** Parse the JSON response to extract relevant fields: review text (body), title, rating, date, etc. AppBot’s API provides fields like `body`, `rating`, `author`, `date`, `country`, and more for each review. At minimum, the summarization agents need the textual content (body or translated_body) of each review.
- **Error Handling:** The integration must handle API errors or rate limits gracefully. (AppBot allows 250k requests/month with bursts of 20/minute.) If the API call fails or returns no data, the system should log an error and halt or retry, rather than proceeding with empty input.
- **Configuration:** The AppBot App ID and API credentials should **not** be hardcoded. These will be provided via environment variables or configuration files. The system should allow specifying filters (e.g., fetch only reviews in English or from last 30 days) if needed, using AppBot API query parameters (the API supports filtering by keyword, country, sentiment, etc.).
- **Output:** The fetched reviews will be aggregated into a suitable format for summarization. For example, combine all review texts into one corpus separated by markers, or prepare a list/array of review snippets. This output will serve as input to the summarizer agents.

### 2. Extractive Summarizer Agent (Deterministic NLP-Based)

- **Description:** An **Extractive Summarizer Agent** that generates a summary by extracting the most significant sentences or phrases from the reviews. This agent uses traditional NLP algorithms (deterministic logic) rather than generating new text. It preserves original wording from the reviews.
- **Technique:** Implement a well-known extractive summarization technique such as TextRank, TF-IDF scoring, or frequency-based selection. For example, using the TextRank algorithm to rank sentences and select the top few for the summary ([5 Powerful Text Summarization Techniques in Python.](https://www.turing.com/kb/5-powerful-text-summarization-techniques-in-python#:~:text=First%2C%20the%20user%20needs%20to,variation%20of%20the%20TextRank%20algorithm)) ([5 Powerful Text Summarization Techniques in Python.](https://www.turing.com/kb/5-powerful-text-summarization-techniques-in-python#:~:text=Since%20TextRank%20is%20a%20graph,information%20drawn%20from%20said%20graphs)). This can be done with Python libraries like **spaCy** (with PyTextRank) or **NLTK/Gensim**. PyTextRank, for instance, supports “low-cost extractive summarization of a text document” ([Download README.md (PyTextRank)](https://sourceforge.net/projects/pytextrank.mirror/files/v3.3.0/README.md/download#:~:text=%2A%20Get%20the%20top,text%20into%20more%20structured%20representation)) by identifying key phrases and sentences.
- **Agent Design:** In CrewAI, this agent can be implemented as a specialized tool or function that the agent calls. The agent’s role is “Extractive Summarizer”; it may not need an LLM for reasoning since the logic is deterministic. We will create a CrewAI `BaseTool` subclass (e.g., `AppReviewExtractiveTool`) that takes the combined review text as input and returns an extractive summary. The agent will invoke this tool directly to produce the result.
- **Output:** The extractive summary should capture the most notable points from the reviews **verbatim**. For example, if many reviews mention “battery life,” a sentence about battery life from a review likely appears in the summary. The output can be a short paragraph or a set of bullet points consisting of sentences directly taken from user reviews. 
- **Determinism & Speed:** Given the same input, this summarizer always produces the same summary (no randomness). It should be relatively fast and computationally lightweight since it’s just text processing. This agent does not require external API calls after the data is fetched, so it can run offline on the input text.
- **Example:** If given 100 app reviews, the extractive agent might return the top 3-5 sentences that represent common themes (e.g., *“The app crashes frequently on startup.”*, *“Love the new features in the latest update.”*, *“Battery usage is too high when running this app.”*).

### 3. Abstractive Summarizer Agent (Probabilistic LLM-Based)

- **Description:** An **Abstractive Summarizer Agent** that uses a Large Language Model (LLM) (specifically OpenAI’s GPT-4o model) to generate a summary in natural language. Unlike the extractive method, this agent will **rewrite** and paraphrase the content of the reviews, producing a summary that may not use the exact original phrases.
- **Technique:** Utilize OpenAI’s GPT-4 (denoted here as GPT-4o) via API to perform text summarization. GPT-4 models are known to handle summarization tasks effectively ([Introduction - Open AI API - The OpenAI API can be applied to virtually any task. We offer a range - Studocu](https://www.studocu.com/in/document/sns-college-of-technology/aircraft-system-and-engines/introduction-open-ai-api/92975037#:~:text=,a%20great%20variety%20of%20tasks)). The agent will prompt the model with the full set of reviews (or a condensed input, if needed) and request a concise summary. For example: *“Summarize the following app reviews in a few sentences, focusing on common feedback and issues.”*
- **Agent Design:** This agent will be configured in CrewAI with an LLM backend. We will set its `llm` attribute to use the GPT-4o model (assuming the OpenAI API is accessible and GPT-4o is a valid model name). No additional tool is needed since the LLM itself performs the summarization. The agent’s role is “Abstractive Summarizer” and its goal is to produce a coherent summary covering the key points from the input text.
- **Output:** The abstractive summary should read like a brief report of user feedback, **in the agent’s own words**. It may combine or rephrase feedback points (e.g., *“Users appreciate the new features but report frequent crashes and high battery usage.”*). The exact wording is generated by the model. Because an LLM is probabilistic, running it twice on the same input could yield slightly different phrasings. We will instruct the model to keep the summary factual and derived from the reviews (to minimize any hallucinations).
- **Considerations:** 
  - **Length & Token Limits:** GPT-4o has a large context window (reports suggest up to 128k tokens for some variants ([How to use o1 or 4o-mini api to analyse and summairze a large text ...](https://community.openai.com/t/how-to-use-o1-or-4o-mini-api-to-analyse-and-summairze-a-large-text-doc-like-over-40k-words-as-a-newbie/946868#:~:text=,as%20input%20and%20summarize%20it))), but we must ensure the input (all reviews text) fits or else chunk the input. For initial implementation, we might limit to a certain number of recent reviews to avoid hitting length limits.
  - **Latency & Cost:** An API call to GPT-4o can be slower and will incur OpenAI API costs. This is acceptable given the improved quality of summary, but we should use it judiciously (e.g., summarizing a batch of reviews rather than one at a time).
  - **Reliability:** The agent should handle API errors (network issues or API rate limits) by catching exceptions. If the OpenAI API fails, the system might fall back to just the extractive summary or retry after a delay.

- **Justification:** Using a model like GPT-4o allows the summary to capture nuances and implied sentiments from reviews, not just explicit sentences. OpenAI’s GPT-series models are explicitly suited for tasks like summarization and creative rewording (models like GPT-4o are known to be good at “summarising long documents” by pulling out key points quickly).

### 4. Comparison and Evaluation Agent (LLM-Based Analysis)

- **Description:** A **Comparison Agent** that evaluates the outputs of the two summarizers (extractive vs. abstractive). This agent uses OpenAI’s **o1 model** (an advanced reasoning LLM) to analyze differences, strengths, and weaknesses of each summary.
- **Purpose:** The goal is to ensure quality and consistency. By comparing the summaries, the agent can identify if the abstractive summary missed an important point that the extractive summary included (or vice versa), and it can provide a judgment on which summary might be more useful or accurate. Essentially, this acts as a QA step powered by an LLM.
- **Agent Design:** The Comparison Agent will be configured with the OpenAI o1 model as its LLM. The agent’s prompt will include both summaries (clearly labeled) and ask the o1 model to analyze them. For example, the prompt could be: *“Here are two summaries of a set of app reviews. Summary A (extractive) and Summary B (abstractive). Compare these summaries: do they cover the same points? Is one more comprehensive or accurate? Provide a brief evaluation.”*
- **Why OpenAI o1:** The o1 series models are optimized for reasoning and complex analysis ([OpenAI o1 explained: Everything you need to know](https://www.techtarget.com/whatis/feature/OpenAI-o1-explained-Everything-you-need-to-know#:~:text=OpenAI%20o1%20explained%3A%20Everything%20you,need%20to%20know)). They excel in tasks requiring step-by-step thought and careful comparison. Using o1 should yield a thoughtful evaluation of the two summaries, as it’s designed to handle complex, multi-step prompts and provide detailed output. (OpenAI’s o1 was launched in late 2024 with enhanced reasoning capabilities for complex tasks ([OpenAI o1 explained: Everything you need to know](https://www.techtarget.com/whatis/feature/OpenAI-o1-explained-Everything-you-need-to-know#:~:text=OpenAI%20o1%20explained%3A%20Everything%20you,need%20to%20know)), making it suitable for evaluating content rather than generating it quickly.)
- **Output:** The output could be a short report or commentary. For instance, the agent might output: *“Both summaries mention new features and crashes. However, Summary A uses the exact words from users, which ensures accuracy but reads less smoothly. Summary B is more concise and fluent, but it omits specific details like battery life complaints that appear in Summary A. Overall, Summary B provides a better general overview, but it misses a critical issue (battery usage) that Summary A included.”* The format can be a few paragraphs or bullet points comparing key aspects (coverage, clarity, correctness).
- **Usage of Comparison:** The system can use this output in a few ways (to be decided in design):
  - Simply log or display the evaluation for a human reviewer (e.g., developers can see how the two methods differ).
  - Or automatically decide which summary to present to end-users based on the comparison (e.g., choose the abstractive summary if it’s deemed better).
  - In this PRD, the primary requirement is generating the comparison, not necessarily autonomously picking the “winner,” but that could be an extension (perhaps the agent’s evaluation could include a recommendation).

### 5. CrewAI Orchestration and Workflow

- **Crew Definition:** Use the CrewAI framework to define a **Crew** that includes the above agents and orchestrates their tasks. CrewAI allows organizing multiple agents with specified roles and a process flow. We will create agents in code or via YAML config, each with the appropriate attributes:
  - **ReviewFetcher Agent (optional):** If needed, an agent (or tool) responsible for calling the AppBot API and providing the raw reviews. This could be a simple tool rather than a full agent, since it’s a straightforward API call returning data.
  - **ExtractiveSummarizer Agent:** Role = “Extractive Summarizer”, Tools = [AppReviewExtractiveTool]. This agent may not use an LLM for generation, as its tool already implements the summarization logic. It takes the reviews text and outputs a summary.
  - **AbstractiveSummarizer Agent:** Role = “Abstractive Summarizer”, LLM = GPT-4o model (with the OpenAI API key configured), no additional tools (unless needed for context management). It takes the same reviews text and outputs a summary.
  - **Comparison Agent:** Role = “Comparison Evaluator”, LLM = OpenAI o1 model, no tools. It takes the two summaries as input and produces the comparative evaluation.
- **Task Sequencing:** The system will manage the execution order of tasks. The likely sequence is:
  1. **Fetch Reviews Task:** (If implemented as a task) The ReviewFetcher agent fetches the reviews from AppBot. *Output:* raw review texts (concatenated or in list form).
  2. **Extractive Summarization Task:** The Extractive agent summarizes the reviews. *Input:* raw reviews from previous step (TaskOutput passed along). *Output:* extractive summary text.
  3. **Abstractive Summarization Task:** The Abstractive agent summarizes the same raw reviews. *Input:* raw reviews (it might fetch from the initial data as well – we can configure tasks to use the original input if needed, or run this in parallel with the extractive task). *Output:* abstractive summary text.
  4. **Comparison Task:** The Comparison agent runs after both summaries are available. *Input:* both summary texts. It uses them to produce an evaluation. *Output:* comparison report.
- **Parallel vs Sequential:** CrewAI supports different process flows (e.g., sequential, parallel). A simple approach is to run tasks sequentially, passing data along, which ensures the summaries are generated one after the other. However, we want both summaries before comparison. We can still use sequential flow: for example, run Extractive Summarization (Task2) and store its output, then run Abstractive Summarization (Task3). After Task3, we have both outputs in the crew’s context or memory. Then Task4 can combine Task2 and Task3 outputs for input. We will ensure the Task4 configuration knows how to retrieve both (perhaps by referencing the previous outputs explicitly or by storing them in a shared location). **Note:** If CrewAI’s API makes it easier, we might run the two summarization agents in parallel threads and synchronize before comparison, but that adds complexity – sequential is acceptable for initial implementation.
- **Data Passing:** Leverage CrewAI’s task output handling. Each task produces a `TaskOutput` object that can carry the `raw` result (and other formats if specified). We will use these outputs as inputs for subsequent tasks:
  - After fetching reviews, both summarizer agents need the reviews text. We might configure both tasks 2 and 3 to use the same output from task 1.
  - After tasks 2 and 3, we will pass their outputs into task 4. This may involve concatenating the two summaries into one input string that the comparison agent’s prompt will consume.
- **Multi-Modal Extendibility:** The design should allow adding more agents or replacing components for multi-modal data in the future. For example, if we later ingest screenshots or video from reviews, we could add:
  - An OCR Agent using a Vision Tool (CrewAI provides a Vision tool for image analysis) to extract text from images.
  - A Speech-to-Text Agent for audio feedback.
  - These could feed into the same summarization agents (after converting non-text input into text), or we could have separate summarizers for different modalities which then combine their results.
  The CrewAI framework’s modular nature (agents with specialized tools) means we can integrate these without altering the core summarization logic – we’d attach new tools and possibly extend the comparison agent to handle additional summary inputs.
- **Logging and Monitoring:** Each agent’s actions should be logged for debugging. CrewAI offers a verbose mode for agents which we can enable during development to trace the reasoning or tool usage ([Agents - CrewAI](https://docs.crewai.com/concepts/agents#:~:text=In%20the%20CrewAI%20framework%2C%20an,an%20autonomous%20unit%20that%20can)). In production, we might keep logging at info level (e.g., when each task starts/ends, any issues encountered).
- **Failure Strategy:** If any component fails (e.g., abstractive summary API call fails), the system should still attempt to produce whatever outputs are possible. For instance, if the GPT-4o call fails, we might still present the extractive summary and note that the abstractive summary is unavailable. The CrewAI crew should ideally handle exceptions so one agent’s failure doesn’t crash the entire run; we might configure tasks with timeouts or fallback behaviors if supported.

---

## Implementation Checklist (with Story-Point Sized Tasks)

Below is a detailed checklist of implementation steps and considerations. Each item is scoped to roughly one “story point” – a small, independent unit of work.

### Project Setup and Configuration

- **Project Structure:** Initialize a new Python project (e.g., `ai_review_summarizer`). Create a clear structure with modules for agents, tools, and tasks. For example:
  - `appbot_client.py` for AppBot API integration functions.
  - `summarizers/` package containing `extractive.py` and `abstractive.py` implementations.
  - `agents/` definitions for CrewAI agents (if using code to define them instead of YAML).
  - A main script (e.g., `run_summary.py`) to orchestrate the execution.
  - Include a `tests/` directory for unit tests.
- **Virtual Environment:** Set up a Python 3.10 virtual environment to isolate dependencies ([Python Virtual Environments - Python Packaging User Guide](https://packaging.python.org/en/latest/specifications/virtual-environments/#:~:text=Guide%20packaging,packages%20directory)). For instance, run `python3.10 -m venv venv` and ensure activation scripts are working. Document this in the README.
- **Dependencies:** Create a `requirements.txt` (or `pyproject.toml` if using Poetry) listing all dependencies:
  - **CrewAI** framework (`crewai` package),
  - **requests** (for API calls),
  - **python-dotenv** (for loading env vars),
  - **spaCy** and **pytextrank** (or alternatively NLTK/Gensim) for extractive summarization,
  - **openai** (OpenAI API client library) for calling GPT-4o and o1,
  - **pytest** (for testing) and possibly **requests-mock** or **pytest-responses** for API call testing.
- **Version Control:** Initialize a git repository. Add a robust `.gitignore` that includes the `venv/`, `.env` file, and other artifacts (like `__pycache__/`). This prevents sensitive info and environment-specific files from being committed.

### Secure Handling of API Keys and Config

- **Environment Variables:** Use environment variables for all sensitive keys and config values (no credentials in code). For example, expect `APPBOT_API_USER` and `APPBOT_API_PASS` for AppBot authentication, and `OPENAI_API_KEY` for OpenAI. Load them at runtime using `os.getenv()`.
- **dotenv Setup:** Utilize **python-dotenv** to load variables from a local `.env` file during development. Call `load_dotenv()` at the program start so that `os.getenv` can pick up values. This allows easy configuration without hardcoding.
- **.env Example:** Provide a `.env.example` file in the repo (with placeholders) to demonstrate required variables. Instruct developers to copy it to `.env` and fill in real keys. 
- **Never Commit Secrets:** Ensure `.env` is in `.gitignore`. Also avoid printing secrets in logs. This adheres to best practices (e.g., OpenAI’s guidelines on API key safety which say never expose keys publicly).
- **Configurable Parameters:** In addition to keys, use config for things like which App ID to fetch, how many reviews to analyze, or which models to use for LLM agents. These can be environment variables or a small config file (like a YAML or JSON loaded at runtime). This makes the system flexible for different apps or different model choices without code changes.

### AppBot API Integration Implementation

- **API Client Function:** Implement a function `fetch_reviews(app_id: str, count: int) -> list[dict]` in `appbot_client.py`. This function uses `requests.get` with the AppBot API endpoint to retrieve reviews. Use `HTTPBasicAuth(APPBOT_API_USER, APPBOT_API_PASS)` from the requests library for authentication.
- **Parameters:** Accept parameters like `app_id` (which app’s reviews to fetch) and possibly `count` or filters (if the API supports limiting number of reviews or filtering by date/rating). The AppBot API can return all reviews by default; if needed, slice the results to the desired count.
- **Parse Response:** After a successful GET (HTTP 200), parse the JSON. AppBot’s response likely contains a list under a key (e.g., `"results"`). Extract each review’s relevant fields into Python objects. For summarization, focus on the review text:
  - Use `review["body"]` or `review["translated_body"]` as the text content (depending on if translations are enabled).
  - Optionally note the rating or other context if needed, but primary input to summarizers is the textual feedback.
- **Return Value:** The function can return a list of review texts or a combined string. For simplicity, consider returning a single large string that concatenates all reviews (perhaps separated by newlines or special tokens). This single text can then be fed to summarizers. Alternatively, return a list of review strings and let each summarizer agent decide how to handle the list (most likely by joining them internally).
- **Error Cases:** Handle non-200 responses. If authentication fails (HTTP 401) or app_id is invalid (404), log an error with details. The function can raise an exception to be caught by the calling workflow. If rate limit exceeded (429), implement a simple retry logic after a short sleep, or at least propagate the error clearly.
- **Testing Consideration:** Ensure this function is written in a way that can be unit tested by injecting a fake response (e.g., allow passing a `requests.Session` or use monkeypatch to simulate `requests.get`). We will test it with a sample JSON structure to verify parsing.

### Extractive Summarizer Agent Implementation

- **NLP Summarization Function:** Implement a function or class method `summarize_extractive(text: str) -> str` in `summarizers/extractive.py`. This will contain the NLP logic for extractive summarization:
  - Split the input text into sentences. (Using spaCy’s English model or NLTK’s sentence tokenizer).
  - Compute importance scores for each sentence. If using TextRank, build a graph of sentence similarities and run the algorithm to rank sentences. Libraries like **Gensim** provide a `summarize()` function that does this with a variation of TextRank ([5 Powerful Text Summarization Techniques in Python.](https://www.turing.com/kb/5-powerful-text-summarization-techniques-in-python#:~:text=First%2C%20the%20user%20needs%20to,variation%20of%20the%20TextRank%20algorithm)). Alternatively, add spaCy’s **pytextrank** pipeline and use it to extract top sentences.
  - Select the top *N* sentences (where N might be configurable, e.g., enough to form a summary of ~100 words or 3 sentences).
  - Preserve the order of those sentences as they appeared in the original text (so the summary is coherent).
- **Output Format:** The output can be a single string with the selected sentences. Optionally, format as bullet points if that improves readability. Since this is primarily for internal comparison and possibly for final output, clarity is key.
- **Integrate with CrewAI:** Wrap this function as a CrewAI tool:
  - Use the `@tool` decorator or subclass `BaseTool` in CrewAI to create `ExtractiveSummaryTool`. This tool’s `run` method will call `summarize_extractive(text)` and return the result. Define the input schema for the tool (likely just a single string field for the text).
  - Add this tool to the Extractive Summarizer Agent’s tool list when configuring the agent. The agent’s prompt or behavior might simply be: “Use your tool to summarize the reviews extractively.” In practice, we might not even need an LLM for this agent; we can directly call the tool in code.
  - If not using an LLM for this agent, we can invoke the tool in the task implementation: i.e., in the CrewAI task for extractive summarization, call `ExtractiveSummaryTool.run()` on the input text to get the summary.
- **Accuracy Check:** Make sure the extractive summary indeed contains the most salient points. We might do some manual tuning: e.g., if the algorithm returns too many sentences, adjust the threshold or number of sentences. This agent’s output will later be judged by the comparison agent, so we want it to be reasonably good (so the comparison is meaningful).
- **Performance:** Loading spaCy and its model can be heavy; do it once at startup (e.g., have a global nlp pipeline if using spaCy). The summarization itself should be quick for a few hundred sentences of input. Ensure this doesn’t become a bottleneck.

### Abstractive Summarizer Agent Implementation

- **OpenAI API Setup:** Install the `openai` Python package and configure it with the API key (e.g., `openai.api_key = os.getenv("OPENAI_API_KEY")` at startup). This allows making requests to GPT-4o.
- **Prompt Design:** In `summarizers/abstractive.py`, define how to prompt GPT-4o for summarization. For instance:
  ```python
  prompt = (
      "You are a helpful AI that summarizes app reviews.\n"
      "Summarize the following user reviews into a short paragraph highlighting common feedback and issues:\n"
      f"{reviews_text}\n"
      "Summary:"
  )
  response = openai.ChatCompletion.create(
      model="gpt-4o", 
      messages=[{"role": "user", "content": prompt}],
      max_tokens=200,
      temperature=0.2  # low temperature for factual consistency
  )
  summary_text = response['choices'][0]['message']['content'].strip()
  ```
  This is a conceptual example. We will fine-tune the prompt as needed and choose parameters like `temperature` to balance creativity and accuracy.
- **Agent Integration:** In CrewAI, configure the Abstractive Summarizer Agent to use the OpenAI GPT-4o LLM. If CrewAI has a setting like `OPENAI_API_KEY` environment variable and model name, it can handle calling the API behind the scenes for the agent. Alternatively, we manually call the OpenAI API as shown above within the task logic.
  - CrewAI might allow something like `Agent(llm="gpt-4o", ...)` and then we just feed the reviews text as the agent’s input/prompt. We'll explore CrewAI’s documentation for using custom prompts or we can use a tool approach: e.g., a tool that calls OpenAI, but it’s simpler to use the agent’s LLM capability directly.
- **Output Handling:** Extract the text returned by the API and consider any post-processing (like removing extra whitespace or ensuring it’s in the desired format). Then package that as the task output.
- **Error Handling:** If the OpenAI API call fails (exception thrown), catch it and mark the task as failed. Possibly include an error message in the output that the comparison agent could see (or simply log it and proceed with whatever is available).
- **Testing (Caution):** It’s hard to unit test the actual API call without making a request. We will abstract the OpenAI call into a function (e.g., `generate_summary_with_gpt(reviews_text)`) that can be mocked in tests. For automated tests, use a dummy function that returns a preset summary. This way, we can test the workflow without hitting the real API. The correctness of GPT’s summary content is assumed based on OpenAI’s quality and is hard to validate automatically; instead we ensure our call is formed correctly.

### Comparison Agent Implementation (OpenAI o1)

- **Prompt and Function:** Implement a function `compare_summaries(summary_extractive: str, summary_abstractive: str) -> str` in `summarizers/compare.py`. This will craft the prompt for the o1 model. For example:
  ```python
  prompt = (
      "You are an expert AI tasked with comparing two summaries of app reviews.\n\n"
      "Summary 1 (Extractive):\n"
      f"{summary_extractive}\n\n"
      "Summary 2 (Abstractive):\n"
      f"{summary_abstractive}\n\n"
      "Compare these summaries in terms of completeness, clarity, and accuracy. "
      "List any important points one summary has that the other lacks. Finally, state which summary is more useful overall or if they are equally good."
  )
  ```
  Then call `openai.ChatCompletion.create` with `model="o1"` (assuming that’s the correct identifier for the o1 model) and the prompt. Since o1 is an advanced model, it might require a slightly different API invocation or have specific options (we’ll refer to OpenAI’s documentation for using o1). The expected output is a text analysis.
- **Agent Setup:** Configure the Comparison Agent in CrewAI with the o1 model as its LLM. Similar to the abstractive agent, we might set `llm="o1"` in the agent definition. The agent can be given a role like “AI Evaluator” with a system prompt that it is analytical and unbiased. However, since we are controlling the prompt each time, the system prompt may be optional.
- **Output Format:** Aim to get a structured response. Possibly instruct the model to format the comparison as bullet points or numbered points for clarity. For example, the prompt might add: “Respond with a brief report, using bullet points for individual observations and a final conclusion.” We must experiment with this to get a clean output.
- **Use of Output:** Determine how to handle the comparison results. This PRD expects the system to **compare** the results; we will at least log or display the o1 model’s evaluation. Optionally, we could parse it to automatically decide on a better summary. For now, treat the output as an end-result (to be shown to developers or users interested in analysis). The final system output could be: the two summaries plus the comparison report.
- **Fallback:** If for some reason the o1 model is unavailable or the call fails, consider falling back to a simpler comparison (like a placeholder message “Comparison not available”). However, since this is a core component, we prefer the system fails obviously rather than silently delivering potentially unvetted summary. Log any issues clearly.

### CrewAI Orchestration Implementation

- **Define Agents in Code or YAML:** Using CrewAI, define the three (or four including fetcher) agents:
  - If using YAML configuration files (`agents.yaml` and `tasks.yaml`), add entries for each agent with fields like `role`, `goal`, `llm`, `tools` etc. Ensure the names match the code references. For example:
    ```yaml
    agents:
      extractive_agent:
        role: Extractive Summarizer
        goal: Summarize reviews by extracting key sentences.
        tools: [extractive_summary_tool]
      abstractive_agent:
        role: Abstractive Summarizer
        goal: Summarize reviews using advanced AI.
        llm: gpt-4o
      comparison_agent:
        role: Comparison Evaluator
        goal: Compare two summaries and evaluate them.
        llm: o1
    ```
    And similarly define tasks that use these agents.
  - Alternatively, define them in Python using CrewAI’s classes:
    ```python
    extractive_agent = Agent(role="Extractive Summarizer", llm=None, tools=[ExtractiveSummaryTool()])
    abstractive_agent = Agent(role="Abstractive Summarizer", llm="gpt-4o")
    comparison_agent = Agent(role="Evaluator", llm="o1")
    ```
    (If `llm=None` or not set for extractive_agent, we rely on the tool output directly.)
- **Define Tasks:** Create Task instances for each step. In code, for example:
  ```python
  fetch_task = Task(description="Fetch app reviews via AppBot API", agent=fetcher_agent)
  extr_task = Task(description="Generate extractive summary of reviews", agent=extractive_agent)
  abs_task  = Task(description="Generate abstractive summary of reviews", agent=abstractive_agent)
  comp_task = Task(description="Compare extractive and abstractive summaries", agent=comparison_agent)
  ```
  The fetch_task might output the reviews text. We need to configure how extr_task and abs_task get that input – possibly by indicating that these tasks depend on fetch_task’s output. CrewAI might allow chaining tasks where the output of one becomes the input context for the next. If not automatic, we will manually feed the data: e.g., after fetch_task, retrieve the reviews text and pass it when invoking the summarizer tasks.
- **Crew Orchestration:** Instantiate a Crew with these agents and tasks, and specify the process order. We can use a sequential process to ensure the tasks run in the correct order. For example:
  ```python
  crew = Crew(agents=[extractive_agent, abstractive_agent, comparison_agent],
              tasks=[fetch_task, extr_task, abs_task, comp_task],
              process=Process.sequential)
  crew.run()
  ```
  This would sequentially execute fetch -> extr -> abs -> comp. (We might adjust if we want extr and abs to run in parallel; CrewAI’s capabilities will determine if parallel execution is feasible. The initial implementation will be sequential for simplicity.)
- **Passing Data Between Tasks:** We will utilize the `TaskOutput`. After running `fetch_task`, the fetched reviews (likely as a string or list) should be accessible. One way is to store it in a variable and then set the input for the next tasks. If using CrewAI’s built-in passing:
  - Ensure `fetch_task` outputs a format that the next tasks can read. If tasks are configured with `expected_output` or similar, we might map the output of fetch_task to a key (like `reviews_text`) that the summarizer tasks know how to consume.
  - Alternatively, within the sequential flow, after fetch_task completes, programmatically set each summarizer agent’s context (or the prompt input) to include the reviews text. For instance, one could do:
    ```python
    reviews = fetch_task.output.raw  # assuming raw text
    extr_task.description = f"Summarize these reviews:\n{reviews}"
    abs_task.description = f"Summarize these reviews:\n{reviews}"
    ```
    so that the tasks have the necessary context. (This might be a workaround if CrewAI doesn’t do it automatically.)
  - For the comparison task, do something similar: after extr_task and abs_task, retrieve their outputs and format the comparison prompt. Possibly directly call the comparison_agent’s LLM with those outputs as we outlined in compare_summaries().
- **Ensure Modularity:** The CrewAI setup should make it easy to add new agents. E.g., if a "Sentiment Analysis Agent" or "Translation Agent" were to be added later, we could insert a task in the sequence or parallel branch. Keep the configuration declarative where possible (YAML), which eases modification without code changes.
- **Validation Run:** After implementation, run the crew on a small sample (maybe a hardcoded few reviews) to verify the pipeline produces the expected outputs at each stage. Adjust any issues in data flow or formatting that cause agents to misinterpret inputs.

### Testing Strategy

- **Unit Tests for API Integration:** Write tests for the AppBot fetch function:
  - Use the `responses` or `requests-mock` library to simulate the HTTP GET response from AppBot. Feed in a sample JSON with a couple of fake reviews and confirm that `fetch_reviews` returns the expected parsed result.
  - Test error handling by simulating non-200 responses (e.g., a 401 Unauthorized) and ensure our code raises an exception or returns a clear error.
- **Unit Tests for Extractive Summarizer:** 
  - If using a library function like Gensim’s summarize, test that our wrapper returns a string of a certain length and that the sentences in the summary actually come from the source text.
  - If we implement TextRank manually, test the ranking on a known input: craft a short paragraph where the most important sentence is known, and verify the function picks it.
  - Test edge cases: empty input (should return empty or a message), extremely short input (summary should be basically the same as input if it’s already very short).
- **Unit Tests for Abstractive Summarizer:** 
  - We will mock the OpenAI API call. For example, monkeypatch `openai.ChatCompletion.create` to return a predefined response payload. Then test that our code properly extracts `summary_text` from it and returns it.
  - Because the actual content is from the model, we focus on testing that the function handles the API call success and failure correctly (e.g., raising a custom exception if API fails).
- **Unit Tests for Comparison Agent:** 
  - Similarly, mock the OpenAI o1 API response. Provide two dummy summaries and simulate an o1 output (we can have a fake response like: "Summary B is more comprehensive.").
  - Test that our comparison function returns a string containing expected keywords or structure that we know the prompt should produce (for instance, if we instruct it to use bullet points, ensure the output starts with a "-" indicating a bullet).
  - Also test that if either summary input is empty, the function still sends a reasonable prompt (the agent might note one summary is missing).
- **Integration Test (CrewAI workflow):** If possible, write a test that runs a small CrewAI crew with stubbed agents:
  - For example, override the Abstractive and Comparison agents to use mock models (to avoid actual API calls) and run the crew on a fixed input. Verify that the final output contains parts from both summaries and the comparison.
  - This can be complex due to threading or asynchronous calls in frameworks, but even a simplified call sequence in a test function could simulate the pipeline: call fetch, then call extractive, then call abstractive (with mock), then call comparison (with mock), and assert on the final results.
- **Test Environment Setup:** Use `pytest` fixtures to load a dummy `.env` so that required env vars are present during tests (but with fake values since we won’t actually call external APIs in unit tests). The `monkeypatch` fixture in pytest can set environment variables for the scope of a test ([How to monkeypatch/mock modules and environments](https://docs.pytest.org/en/7.1.x/how-to/monkeypatch.html#:~:text=How%20to%20monkeypatch%2Fmock%20modules%20and,path%20for%20importing)), which we’ll use to set `OPENAI_API_KEY` etc., to avoid the code complaining.
- **Continuous Testing:** Incorporate these tests in a CI pipeline if available. Ensure that any change to summarization logic or prompts still passes tests (though for LLM outputs, tests will be more about structure than exact text).
- **Quality Assurance:** In addition to automated tests, perform manual testing with actual API calls (especially for the abstractive and comparison agents) to see the quality of summaries and comparisons. Tweak parameters or prompts based on these tests. This manual QA is important given the dynamic nature of LLM outputs.

### Documentation and README Requirements

- **Comprehensive README:** Prepare a detailed `README.md` covering the following:
  - **Project Overview:** Explain what the application does (summarizes app reviews with a hybrid approach and compares results). Mention the motivation and the high-level architecture (CrewAI multi-agent workflow). This introduction helps readers (or stakeholders) grasp the purpose quickly.
  - **Setup Instructions:** Provide step-by-step instructions to set up the environment. e.g.:
    1. Clone the repository.
    2. Create a Python 3.10 virtual environment and activate it.
    3. Install dependencies using `pip install -r requirements.txt`.
    4. Create a `.env` file based on `.env.example` and input the required API keys.
  - **Configuration:** Document all environment variables and configuration options. For example:
    - `APPBOT_API_USER` and `APPBOT_API_PASS`: how to obtain them (e.g., from AppBot dashboard, generate API key v2).
    - `APPBOT_APP_ID`: the identifier of the app whose reviews will be analyzed.
    - `OPENAI_API_KEY`: for GPT-4o and o1 usage (one key covers both if using OpenAI API).
    - Possibly options like number of reviews to fetch or summary length if we made those configurable.
  - **Usage:** Explain how to run the summarization. If it’s a command-line tool, provide an example command. If it’s a script, mention `python run_summary.py` and what it will do. Also describe the output: e.g., “The program will output three sections: the extractive summary, the abstractive summary, and an evaluation report.” If the output is saved to a file (optional feature), note the file location.
  - **CrewAI Details:** Briefly mention how CrewAI is used (the concept of agents and tasks). This gives credit and context, and if someone needs to modify the workflow, they know it’s configured via CrewAI. If YAML configs are used, point to those files for reference. You might also cite CrewAI’s documentation for further reading.
  - **Example:** Provide an example scenario. It could be fictional data or a real small set of reviews (if license permits). Show what the extractive summary and abstractive summary look like, and include a sample of the comparison agent’s output. This helps users verify their run is correct and see the value of the tool.
  - **Extensibility Notes:** Include a section on future improvements, especially the plan for multi-modal inputs. For instance, *“The architecture is designed to be extensible. In the future, we can add agents for image or audio analysis (e.g., using OCR on screenshots of reviews) and feed their output into the summarization pipeline. CrewAI will allow adding these agents and corresponding tasks with minimal changes to the existing ones.”* This signals that the current design choices have considered the upcoming features.
  - **Contribution Guide (if applicable):** If this is a team or open-source project, outline how others can contribute. E.g., “Please open an issue for bugs or request to add new summarization techniques. Ensure new code passes all tests. We welcome pull requests.”
  - **License and Acknowledgments:** State the project license. Acknowledge any third-party libraries (CrewAI, etc.) and data sources (if any).
- **Inline Code Documentation:** In addition to the README, ensure the code itself is well-commented. Especially document the prompt engineering parts (so future developers understand why we phrased prompts in a certain way) and any non-obvious logic in the summarization algorithms.
- **API Documentation:** If time permits, you could generate docs for the code using a tool like Sphinx or pydoc. However, given this is an internal app, well-written docstrings for each function might suffice. For example, docstring for `summarize_extractive` explaining the algorithm, or for `compare_summaries` explaining the prompt structure.
- **Diagrams:** Optionally, include a simple diagram in the README illustrating the agent workflow (e.g., a flowchart: AppBot API -> [Reviews] -> Extractive Agent -> [Summary A] -> Comparison Agent; AppBot API -> [Reviews] -> Abstractive Agent -> [Summary B] -> Comparison Agent -> [Evaluation]). This can be added later, but even an ASCII or text outline of flow can help readers.
- **Ensure Clarity:** The README should be written in clear language, avoiding overly technical jargon when explaining to an interested stakeholder. It should highlight the real-world relevance: for instance, how this tool can help product teams quickly understand user feedback trends by summarizing large volumes of reviews.

By following this implementation plan and checklist, we will build a robust application that **summarizes app reviews using both extractive and abstractive methods and compares the results**. Each component will be modular, testable, and maintainable, with clear documentation for users and developers. The use of CrewAI will orchestrate the agents’ collaboration, demonstrating a practical example of hybrid AI agents working together to enhance insight from textual data. 

**Sources:**

1. AppBot API – Overview of review data and usage  
2. CrewAI Framework – Multi-agent orchestration and task management ([Introduction - CrewAI](https://docs.crewai.com/introduction#:~:text=CrewAI%20is%20a%20lean%2C%20lightning,LangChain%20or%20other%20agent%20frameworks))  
3. Extractive Summarization – Techniques like TextRank for key sentence extraction ([5 Powerful Text Summarization Techniques in Python.](https://www.turing.com/kb/5-powerful-text-summarization-techniques-in-python#:~:text=First%2C%20the%20user%20needs%20to,variation%20of%20the%20TextRank%20algorithm)) ([Download README.md (PyTextRank)](https://sourceforge.net/projects/pytextrank.mirror/files/v3.3.0/README.md/download#:~:text=%2A%20Get%20the%20top,text%20into%20more%20structured%20representation))  
4. Abstractive Summarization with GPT-4 – Using LLMs for summarizing text ([Introduction - Open AI API - The OpenAI API can be applied to virtually any task. We offer a range - Studocu](https://www.studocu.com/in/document/sns-college-of-technology/aircraft-system-and-engines/introduction-open-ai-api/92975037#:~:text=,a%20great%20variety%20of%20tasks))  
5. OpenAI o1 Model – Enhanced reasoning for complex comparative analysis ([OpenAI o1 explained: Everything you need to know](https://www.techtarget.com/whatis/feature/OpenAI-o1-explained-Everything-you-need-to-know#:~:text=OpenAI%20o1%20explained%3A%20Everything%20you,need%20to%20know))  
6. Environment & Security – Handling API keys via environment variables