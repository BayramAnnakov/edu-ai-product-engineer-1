"""
Multi-Agent User Board Simulation Pipeline

This script orchestrates an end-to-end pipeline for simulating user board discussions.
"""

from __future__ import annotations

import json
import logging
import os
import random
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple, TypedDict

import numpy as np
from dotenv import load_dotenv
from langchain.schema import AIMessage, BaseMessage, HumanMessage
from langchain_community.callbacks.manager import get_openai_callback
from langchain_core.exceptions import LangChainException
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from rich.logging import RichHandler
from tenacity import retry, stop_after_attempt, wait_fixed
from openai import APIError
from langchain.chains import ConversationChain

from board_simulation import simulate_userboard
from data_types import Persona, FeatureProposal
# --- Import the new persona generator function ---
from persona_generator import generate_personas

# --- Determine Project Root and Load Env ---
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR

env_path = PROJECT_ROOT / ".env"
if not env_path.exists():
    print(f"Warning: .env file not found at {env_path}. Ensure OPENAI_API_KEY is set via environment variables.")
load_dotenv(dotenv_path=env_path)

# -----------------------------------------------------------------------------
# Configuration & Constants
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class Config:
    """Project-wide constants."""
    cluster_json: Path = PROJECT_ROOT / "cluster_outputs" / "clusters_data.json"
    output_dir: Path = PROJECT_ROOT / "multiagent_outputs"
    model_name: str = "gpt-4.1"
    temperature: float = 0.5
    persona_count: int = 5
    feature_count: int = 3
    discussion_rounds: int = 3
    random_seed: int | None = 42

CFG = Config()
CFG.output_dir.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# Logging Setup
# -----------------------------------------------------------------------------
log_path = CFG.output_dir / "board_session.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(module)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[RichHandler(rich_tracebacks=True, show_path=False),
              logging.FileHandler(log_path, "w", "utf-8")],
    force=True
)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
logger.info("Logging initialized. Log file: %s", log_path)
logger.info("Using configuration: %s", CFG)

# -----------------------------------------------------------------------------
# Utility Dataclasses & State Definition
# -----------------------------------------------------------------------------
class AgentState(TypedDict):
    """Defines the state passed between graph nodes."""
    selected_clusters: Dict[str, dict]
    features: List[FeatureProposal]
    personas: List[Persona]
    transcript: str
    conversation_history: List[BaseMessage]
    summary: str
    error: str | None


# -----------------------------------------------------------------------------
# LLM Wrapper with Retry Logic
# -----------------------------------------------------------------------------
LLM = ChatOpenAI(model=CFG.model_name, temperature=CFG.temperature)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    reraise=True
)
def invoke_llm_with_retry(llm_client: ChatOpenAI, messages: List[BaseMessage]) -> str:
    """Invokes the LLM with retry logic for transient errors."""
    logger.debug("Invoking LLM with %d messages...", len(messages))
    try:
        response = llm_client.invoke(messages)
        reply = response.content.strip()
        logger.debug("LLM reply received (first 100 chars): %s", reply[:100])
        return reply
    except APIError as e:
        logger.error("OpenAI API Error during LLM call: %s", e, exc_info=True)
        raise
    except LangChainException as e:
        logger.error("LangChain Error during LLM call: %s", e, exc_info=True)
        raise
    except Exception as e:
        logger.error("Unexpected error during LLM call: %s", e, exc_info=True)
        raise

def ask_llm(prompt: str) -> str:
    """Synchronous LLM call using the retry wrapper."""
    logger.debug("ask_llm prompt (first 200 chars): %s", prompt[:200] + ("…" if len(prompt) > 200 else ""))
    return invoke_llm_with_retry(LLM, [HumanMessage(content=prompt)])

# -----------------------------------------------------------------------------
# Cluster Data Loading and Selection
# -----------------------------------------------------------------------------
def load_cluster_data(path: Path) -> Dict[str, dict]:
    """Loads cluster data from JSON, handling list or dict format."""
    logger.info("Loading cluster data from: %s", path)
    if not path.exists():
        logger.error("Cluster JSON file not found at %s", path)
        raise FileNotFoundError(f"Cluster JSON file not found: {path}")

    try:
        with path.open(encoding="utf-8") as f:
            loaded_data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error("Failed to decode JSON from %s: %s", path, e)
        raise ValueError(f"Invalid JSON file: {path}") from e
    except Exception as e:
        logger.error("Failed to read cluster file %s: %s", path, e)
        raise IOError(f"Could not read cluster file: {path}") from e

    clusters: Dict[str, dict]
    if isinstance(loaded_data, list):
        clusters = {str(i): item for i, item in enumerate(loaded_data)}
        logger.info("Loaded cluster data as list, converted to dict using string indices (0 to %d).", len(clusters) - 1)
    elif isinstance(loaded_data, dict):
        clusters = loaded_data
        logger.info("Loaded cluster data as dict.")
    else:
        logger.error("Unexpected data type loaded from JSON: %s. Expected dict or list.", type(loaded_data))
        raise TypeError(f"Unexpected data type in JSON file: {type(loaded_data)}")

    if not clusters:
        logger.error("Cluster data is empty after loading/processing.")
        raise ValueError("Cluster data is empty.")

    for key, value in clusters.items():
        if not isinstance(value, dict) or 'keywords' not in value or 'sentiment_dist' not in value:
            logger.warning("Cluster '%s' might be missing expected keys ('keywords', 'sentiment_dist').", key)

    logger.info("Successfully loaded and validated %d clusters.", len(clusters))
    return clusters


def pick_top_clusters(clusters: Dict[str, dict], k: int) -> Dict[str, dict]:
    """Selects top k clusters, ranked by negative sentiment count."""
    if k <= 0:
        return {}
    try:
        ranked = sorted(
            clusters.items(),
            key=lambda kv: kv[1].get('sentiment_dist', {}).get("negative", 0) if isinstance(kv[1], dict) else 0,
            reverse=True,
        )
    except Exception as e:
        logger.error("Error sorting clusters: %s. Check cluster data format.", e, exc_info=True)
        raise TypeError("Cluster data format seems incompatible for sorting.") from e

    num_to_select = min(k, len(ranked))
    if num_to_select < k:
        logger.warning("Requested %d clusters, but only %d available after ranking.", k, num_to_select)

    selected = dict(ranked[:num_to_select])
    logger.info("Selected top %d clusters for ideation: %s", len(selected), list(selected.keys()))
    return selected

# -----------------------------------------------------------------------------
# Feature Ideation and Persona Generation
# -----------------------------------------------------------------------------
def ideate_features(selected: Dict[str, dict], n: int = CFG.feature_count) -> List[FeatureProposal]:
    """Generates feature proposals based on selected clusters using an LLM."""
    logger.info("Starting feature ideation for %d features...", n)
    if not selected:
        logger.warning("No clusters selected for feature ideation.")
        return []

    cluster_details = []
    for cid, info in selected.items():
        if not isinstance(info, dict):
            logger.warning("Skipping cluster '%s' in ideation prompt due to unexpected format: %s", cid, type(info))
            continue

        keywords = ', '.join(info.get('keywords', ['N/A']))
        neg_sentiment = info.get('sentiment_dist', {}).get('negative', 0)
        samples = info.get('samples', [])
        sample_feedback = samples[0] if samples else 'N/A'

        cluster_details.append(
            f"- **Cluster {cid}**:\n"
            f"  - Keywords: {keywords}\n"
            f"  - Negative Sentiment Count: {neg_sentiment}\n"
            f"  - Sample Feedback: '{sample_feedback[:200]}...'")

    if not cluster_details:
        logger.error("No valid cluster details could be extracted for the feature ideation prompt.")
        return []

    cluster_str = "\n".join(cluster_details)

    prompt = (
        f"You are a Senior Product Manager at Spotify, specializing in user experience. "
        f"Your task is to propose exactly {n} concrete and realistic product features or UX improvements "
        f"that directly address the pain points highlighted in the following user feedback clusters. "
        f"Focus on actionable solutions that enhance user satisfaction.\n\n"
        f"**User Feedback Clusters:**\n"
        f"{cluster_str}\n\n"
        f"**Instructions:**\n"
        f"1. Generate exactly {n} distinct feature proposals.\n"
        f"2. Each proposal should be a clear, concise imperative statement.\n"
        f"3. Ensure the features directly relate to the pain points identified in the cluster keywords and sample feedback.\n"
        f"4. Return EACH proposal on a new line, with NO prefixes and NO blank lines between proposals.\n\n"
        f"**Example Output Format:**\n"
        f"Allow collaborative playlist editing in real-time\n"
        f"Introduce higher fidelity audio options for subscribers\n"
        f"Simplify the podcast discovery interface"
    )

    try:
        raw = ask_llm(prompt)
        lines = [line.strip() for line in raw.split('\n') if line.strip()]
        proposals_text = [line for line in lines if not line.startswith(("*", "-", "#")) and "|" not in line]

        proposals = [FeatureProposal(id=i + 1, description=desc) for i, desc in enumerate(proposals_text[:n])]

        if len(proposals) < n:
            logger.warning("LLM generated fewer than %d valid proposals. Got %d. Raw output:\n%s", n, len(proposals), raw)
        elif len(proposals) > n:
            logger.warning("LLM generated more than %d proposals. Taking the first %d. Raw output:\n%s", n, n, raw)
            proposals = proposals[:n]

        logger.info("Feature ideation complete. Generated %d features: %s", len(proposals), [p.description for p in proposals])
        return proposals

    except Exception as e:
        logger.error("Feature ideation failed: %s", e, exc_info=True)
        return []

# -----------------------------------------------------------------------------
# Board Simulation and Meeting Summary
# -----------------------------------------------------------------------------
def summarise_meeting(transcript_md: str, conversation_history: List[BaseMessage] | None = None) -> str:
    """Summarizes the virtual board meeting transcript using an LLM."""
    logger.info("Generating meeting summary...")
    if not transcript_md.strip():
        logger.warning("Transcript is empty, cannot generate summary.")
        return "Error: Transcript was empty."

    prompt = (
        "You are an expert meeting summarizer. Analyze the virtual user board meeting transcript provided below.\n"
        "Your summary MUST include these sections in markdown format:\n\n"
        "1. **Pros & Cons per Feature:** For each proposed feature, list the key advantages (Pros) and disadvantages or concerns (Cons) raised by the participants. Be specific.\n"
        "2. **Overall Sentiment & Key Takeaways per Persona:** Briefly describe each persona's overall stance, highlighting their main points, priorities, or key concerns.\n"
        "3. **Points of Agreement & Disagreement:** Note any areas where personas strongly agreed or disagreed with each other.\n"
        "4. **Final Recommendation:** Provide a concise (1-3 sentences) go/no-go/conditional recommendation for the features, explicitly mentioning the rationale based on the discussion.\n\n"
        "---\n"
        f"{transcript_md}\n"
        "---\n"
        "Generate the summary now."
    )

    try:
        summary = ask_llm(prompt)
        logger.info("Meeting summary generated successfully.")
        return summary
    except Exception as e:
        logger.error("Failed to generate meeting summary: %s", e, exc_info=True)
        return f"Error: Failed to generate meeting summary due to: {e}"

# -----------------------------------------------------------------------------
# Report Writing and Main Pipeline
# -----------------------------------------------------------------------------
def write_report(
    selected_clusters: Dict[str, dict],
    features: Sequence[FeatureProposal],
    personas: Sequence[Persona],
    transcript: str,
    summary: str
):
    """Writes the final Markdown report to the output directory."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    report_path = CFG.output_dir / "board_session_report.md"
    logger.info("Writing final report to: %s", report_path)

    try:
        with report_path.open("w", encoding="utf-8") as f:
            f.write("# 🎵 Spotify Virtual User-Board Session\n\n")
            f.write(f"*Generated on {ts}*\n\n")
            f.write("## 📊 Overview\n\n")
            f.write(f"- **Number of Features Discussed**: {len(features)}\n")
            f.write(f"- **Number of Personas**: {len(personas)}\n")
            f.write(f"- **Discussion Rounds**: {CFG.discussion_rounds}\n\n")

            f.write("## 🔍 Selected User Feedback Clusters\n\n")
            for cluster_id, cluster_data in sorted(selected_clusters.items(), key=lambda item: str(item[0])):
                f.write(f"### Cluster {cluster_id}\n\n")
                keywords = cluster_data.get('keywords', [])
                f.write(f"- **Keywords**: {', '.join(keywords)}\n")
                sentiment_dist = cluster_data.get('sentiment_dist', {})
                f.write("- **Sentiment Distribution**:\n")
                for sentiment, count in sorted(sentiment_dist.items()):
                    f.write(f"  - {sentiment.capitalize()}: {count}\n")
                f.write("- **Sample Feedback**:\n")
                samples = cluster_data.get('samples', [])
                for sample in samples[:2]:
                    cleaned_sample = sample.strip()
                    f.write(f"  > {cleaned_sample}\n")
                f.write("\n")

            f.write("## 💡 Proposed Features\n\n")
            if features:
                for feat in features:
                    f.write(f"### {feat.md()}\n\n")
            else:
                f.write("*No features were generated.*\n\n")

            f.write("## 👥 User Personas\n\n")
            if personas:
                for persona in personas:
                    f.write(persona.md())
                    f.write("\n")
            else:
                f.write("*No personas were generated.*\n\n")

            f.write("## 💬 Discussion Transcript\n\n")
            if transcript.strip():
                f.write("```markdown\n")
                f.write(transcript + "\n")
                f.write("```\n\n")
            else:
                f.write("*No discussion transcript was generated.*\n\n")

            f.write("## 📝 Meeting Summary\n\n")
            if summary.strip() and not summary.startswith("Error:"):
                f.write(summary + "\n")
            else:
                f.write(f"*Summary could not be generated. Details: {summary}*\n")

            f.write("\n---\n")
            f.write("*This report was generated using an AI-powered user board simulation pipeline.*\n")

        logger.info("Markdown report written successfully.")

    except IOError as e:
        logger.error("Failed to write report file %s: %s", report_path, e, exc_info=True)
    except Exception as e:
        logger.error("An unexpected error occurred during report writing: %s", e, exc_info=True)


async def run_board_simulation(state: AgentState) -> Dict[str, Any]:
    if state.get("error"): return {}
    try:
        transcript_md, history = await simulate_userboard(state["personas"], state["features"], CFG.discussion_rounds)
        return {"transcript": transcript_md, "conversation_history": history, "error": None}
    except Exception as e:
        logger.error("Error in board simulation node: %s", e, exc_info=True)
        return {"error": f"Board Simulation Failed: {e}"}

def build_pipeline():
    """Builds the LangGraph StateGraph pipeline."""
    logger.info("Building LangGraph pipeline...")
    graph = StateGraph(AgentState)

    def run_feature_ideation(state: AgentState) -> Dict[str, Any]:
        try:
            features = ideate_features(state["selected_clusters"], CFG.feature_count)
            return {"features": features, "error": None}
        except Exception as e:
            logger.error("Error in feature ideation node: %s", e, exc_info=True)
            return {"error": f"Feature Ideation Failed: {e}"}

    def run_persona_generation(state: AgentState) -> Dict[str, Any]:
        if state.get("error"): return {}
        try:
            # Pass ask_llm function to the generator
            personas = generate_personas(
                clusters=state["selected_clusters"],
                count=CFG.persona_count,
                ask_llm_func=ask_llm
            )
            return {"personas": personas, "error": None}
        except Exception as e:
            logger.error("Error in persona generation node: %s", e, exc_info=True)
            return {"error": f"Persona Generation Failed: {e}"}

    def run_summary_generation(state: AgentState) -> Dict[str, Any]:
        if state.get("error"): return {}
        try:
            summary = summarise_meeting(state["transcript"], state["conversation_history"])
            return {"summary": summary, "error": None}
        except Exception as e:
            logger.error("Error in summary generation node: %s", e, exc_info=True)
            return {"error": f"Summary Generation Failed: {e}"}

    graph.add_node("ideate", run_feature_ideation)
    graph.add_node("generate_personas", run_persona_generation)
    graph.add_node("board", run_board_simulation)
    graph.add_node("generate_summary", run_summary_generation)

    graph.set_entry_point("ideate")
    graph.add_edge("ideate", "generate_personas")
    graph.add_edge("generate_personas", "board")
    graph.add_edge("board", "generate_summary")
    graph.add_edge("generate_summary", END)

    pipeline = graph.compile()
    logger.info("LangGraph pipeline compiled successfully.")
    return pipeline


async def main() -> None:
    """Main function to load data, build and run the pipeline, and write the report."""
    if CFG.random_seed is not None:
        random.seed(CFG.random_seed)
        np.random.seed(CFG.random_seed)
        logger.info("Using random seed: %d", CFG.random_seed)

    try:
        clusters = load_cluster_data(CFG.cluster_json)
        selected_clusters_data = pick_top_clusters(clusters, k=CFG.persona_count)
        if not selected_clusters_data:
            logger.error("No clusters were selected. Cannot proceed.")
            sys.exit(1)

        pipeline = build_pipeline()

        initial_state: AgentState = {
            "selected_clusters": selected_clusters_data,
            "features": [],
            "personas": [],
            "transcript": "",
            "conversation_history": [],
            "summary": "",
            "error": None
        }

        logger.info("Invoking pipeline...")
        final_state = await pipeline.ainvoke(initial_state)
        logger.info("Pipeline invocation complete.")

        if final_state.get("error"):
            logger.error("Pipeline execution failed with error: %s", final_state["error"])
            logger.warning("Attempting to write partial report despite pipeline error...")

        write_report(
            final_state.get("selected_clusters", selected_clusters_data),
            final_state.get("features", []),
            final_state.get("personas", []),
            final_state.get("transcript", "*Transcript generation failed or skipped due to error.*"),
            final_state.get("summary", f"*Summary generation failed or skipped. Error: {final_state.get('error')}*")
        )

        if final_state.get("error"):
            logger.error("Pipeline finished with errors.")
            sys.exit(1)
        else:
            logger.info("✅ Multi-agent pipeline finished successfully.")

    except FileNotFoundError as e:
        logger.error("❌ Pipeline failed: Required file not found.")
        logger.error(e, exc_info=True)
        sys.exit(2)
    except ValueError as e:
        logger.error("❌ Pipeline failed: Data validation or processing error.")
        logger.error(e, exc_info=True)
        sys.exit(3)
    except Exception as e:
        logger.error("❌ Pipeline failed with an unexpected error.")
        logger.error(e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())