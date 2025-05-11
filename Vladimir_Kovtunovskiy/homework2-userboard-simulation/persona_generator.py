"""
Functions for generating user personas based on cluster data using an LLM.
"""

import json
import logging
from typing import Any, Callable, Dict, List, Tuple
from data_types import Persona

logger = logging.getLogger(__name__)


def _build_persona_prompt(clusters_data: List[Tuple[str, dict]], count: int) -> str:
    """Builds the LLM prompt for generating personas."""
    cluster_details_list = []
    for cluster_id, cluster_data in clusters_data:
        if not isinstance(cluster_data, dict):
            logger.warning(f"Skipping cluster '{cluster_id}' in prompt due to invalid format.")
            continue

        keywords_str = ", ".join(cluster_data.get('keywords', ['N/A']))
        sentiment_dist = cluster_data.get('sentiment_dist', {})
        samples = cluster_data.get('samples', [])
        sample_feedback = samples[0] if samples else 'N/A'
        sentiment_info = f"SentimentDist=[{', '.join(f'{k}: {v}' for k, v in sentiment_dist.items())}]"
        if 'avg_sentiment' in cluster_data:
            sentiment_info += f" | AvgSentiment={cluster_data['avg_sentiment']:.2f}"

        cluster_details_list.append(
            f'- Cluster {cluster_id}: Keywords=[{keywords_str}] | {sentiment_info} | Sample="{sample_feedback[:150]}..."'
        )

    if not cluster_details_list:
        logger.error("No valid cluster details could be extracted for persona generation prompt.")
        return ""

    cluster_summary_str = "\n".join(cluster_details_list)

    # Consistent JSON format example for the prompt
    json_format_example = """
    ```json
    [
      {
        "name": "Alex Chen",
        "background": "Deep, diverse description of the persona's background in 5-10 sentences",
        "quote": "Finding new music I actually like feels harder than it should be.",
        "sentiment": "neutral",
        "pain_points": [
          "Music discovery algorithm often misses the mark",
          "Too many ads in the free tier interrupt listening flow",
          "Playlist organization options are limited"
        ],
        "inspired_by_cluster_id": "3"
      }
    ]
    ```
    """

    # Using f-string for the entire prompt for clarity
    prompt = f"""You are an expert persona generator specializing in user experience research. Your task is to create exactly {count} distinct and deeply grounded Spotify user personas based on the provided user feedback cluster summaries.

**Requirements:**
1. Generate {count} Personas
2. Ensure personas have unique backgrounds, motivations, Spotify usage patterns, and personalities.
3. Each persona's details MUST directly reflect themes from the provided cluster summaries.
4. Use ONLY 'positive', 'neutral', or 'negative' for the `sentiment` field.
5. List specific, concrete frustrations or challenges the user faces with Spotify.
6. Return ONLY a valid JSON list containing the persona objects. NO other text before or after the JSON list.

**Cluster Summaries:**
{cluster_summary_str}

**Required JSON Format Example:**
{json_format_example}

Generate the JSON output now. Remember to:
- Start with [
- End with ]
- Include all required fields for each persona
- Do not add any text before or after the JSON list
- Ensure the JSON is properly formatted and valid"""
    return prompt


def _parse_llm_persona_response(raw_response: str) -> List[Dict[str, Any]] | None:
    """Cleans, parses, and validates the structure of the LLM JSON response."""
    logger.debug("Raw LLM response for persona generation (first 500 chars): %s...", raw_response[:500])
    cleaned_response = raw_response.strip()

    # Remove potential markdown code fences more robustly
    if cleaned_response.startswith("```json"):
        cleaned_response = cleaned_response[7:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
    elif cleaned_response.startswith("```"): # Handle cases with just ``` at the start
        cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith("```"):
             cleaned_response = cleaned_response[:-3]

    cleaned_response = cleaned_response.strip() # Strip again after removing fences

    if not cleaned_response.startswith("[") or not cleaned_response.endswith("]"):
        logger.error("LLM response for personas is not a valid JSON list. Preview: %s...", cleaned_response[:200])
        return None

    try:
        parsed_json = json.loads(cleaned_response)
        if not isinstance(parsed_json, list):
            logger.error("Parsed JSON is not a list. Type: %s", type(parsed_json))
            return None
        return parsed_json
    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON from LLM response. Error: %s. Preview: %s...", e, cleaned_response[:200])
        return None


def _validate_and_create_persona(persona_data: Dict[str, Any], index: int) -> Persona | None:
    """Validates a single persona dictionary and creates a Persona object."""
    if not isinstance(persona_data, dict):
        logger.warning(f"Skipping item #{index+1} in JSON response: not a dictionary.")
        return None

    required_keys = {"name", "background", "quote", "sentiment", "pain_points", "inspired_by_cluster_id"}
    actual_keys = set(persona_data.keys())
    if not required_keys.issubset(actual_keys):
        missing = required_keys - actual_keys
        extra = actual_keys - required_keys
        warning_msg = f"Skipping persona #{index+1}:"
        if missing:
            warning_msg += f" Missing required keys: {missing}."
        if extra:
            warning_msg += f" Found unexpected keys: {extra}."
        warning_msg += f" Data: {persona_data}"
        logger.warning(warning_msg)
        return None

    name = persona_data.get("name")
    sentiment = persona_data.get("sentiment", "").lower()
    pain_points = persona_data.get("pain_points", [])
    cluster_id_raw = persona_data.get("inspired_by_cluster_id")

    # Validate sentiment
    if sentiment not in ["positive", "neutral", "negative"]:
        logger.warning(f"Skipping persona '{name or 'Unknown'}': Invalid sentiment '{persona_data.get('sentiment')}'. Must be 'positive', 'neutral', or 'negative'.")
        return None

    # Validate pain_points format
    if not isinstance(pain_points, list) or not all(isinstance(p, str) for p in pain_points):
        logger.warning(f"Skipping persona '{name or 'Unknown'}': Invalid 'pain_points' format (must be a list of strings).")
        return None

    # Process inspired_by_cluster_id: Allow null/None, ensure it's string if present
    cluster_id = None
    if cluster_id_raw is not None:
        if isinstance(cluster_id_raw, str):
            cluster_id = cluster_id_raw
        else:
            try:
                cluster_id = str(cluster_id_raw)
                logger.debug(f"Converted non-string cluster_id '{cluster_id_raw}' to string for persona '{name}'.")
            except Exception:
                logger.warning(f"Persona '{name or 'Unknown'}': Could not convert 'inspired_by_cluster_id' to string: {cluster_id_raw}. Setting to None.")
                cluster_id = None # Set to None if conversion fails

    # Attempt to create the Persona object
    try:
        return Persona(
            name=str(persona_data.get("name", "")), # Ensure name is string
            background=str(persona_data.get("background", "")), # Ensure background is string
            quote=str(persona_data.get("quote", "")), # Ensure quote is string
            sentiment=sentiment, # Already validated
            pain_points=[str(p) for p in pain_points], # Ensure all points are strings
            inspired_by_cluster_id=cluster_id # Processed above
        )
    except TypeError as e:
        logger.warning(f"Skipping persona '{name or 'Unknown'}' due to TypeError during instantiation (likely bad data type): {e}. Data: {persona_data}")
        return None
    except Exception as e: # Catch other potential errors during Persona instantiation
        logger.warning(f"Skipping persona '{name or 'Unknown'}' due to unexpected instantiation error: {e}. Data: {persona_data}")
        return None


def generate_personas(
    clusters: Dict[str, dict],
    count: int,
    ask_llm_func: Callable[[str], str]
) -> List[Persona]:
    """Generates diverse user personas based on cluster data using an LLM.

    Args:
        clusters: Dictionary containing cluster data.
        count: The target number of personas to generate.
        ask_llm_func: A callable function that takes a prompt string and returns
                      the LLM response string.

    Returns:
        A list of generated Persona objects.
    """
    if not clusters:
        logger.warning("No clusters provided for persona generation.")
        return []
    if count <= 0:
        logger.warning("Requested persona count is zero or negative.")
        return []

    # Select clusters to use for prompt generation
    cluster_items = list(clusters.items())
    num_clusters_available = len(cluster_items)
    num_to_select = min(count, num_clusters_available)

    if num_to_select < count:
        logger.warning(f"Requested {count} personas, but only {num_clusters_available} clusters available. Generating based on {num_to_select}.")
    elif num_to_select == 0:
        logger.warning("No clusters available to generate personas from.")
        return []

    selected_clusters_for_prompt = cluster_items[:num_to_select]

    # 1. Build Prompt
    prompt = _build_persona_prompt(selected_clusters_for_prompt, count)
    if not prompt:
        logger.error("Persona generation prompt could not be built.")
        return []

    # 2. Call LLM via the provided function
    try:
        raw_response = ask_llm_func(prompt)
    except Exception as e:
        logger.error(f"LLM call via ask_llm_func failed during persona generation: {e}", exc_info=True)
        return []

    # 3. Parse Response
    parsed_json = _parse_llm_persona_response(raw_response)
    if parsed_json is None:
        logger.error("Failed to parse LLM response for persona generation.")
        return []

    # 4. Validate and Create Personas from parsed data
    personas: List[Persona] = []
    validated_count = 0
    for i, item_data in enumerate(parsed_json):
        persona = _validate_and_create_persona(item_data, i)
        if persona:
            personas.append(persona)
            validated_count += 1
            # Stop if we have generated the required number of *valid* personas
            if validated_count == count:
                logger.info(f"Successfully generated requested number ({count}) of valid personas.")
                break

    logger.info(f"Processed LLM response. Successfully validated {validated_count} personas.")

    # Handle cases where the final count doesn't match the requested count
    if validated_count < count:
        logger.warning(f"Generated fewer valid personas ({validated_count}) than requested ({count}). Check LLM output and validation logic.")
    # If validated_count > count, it means the LLM returned more valid items than requested,
    # but the loop breaks once `count` is reached, so we only return `count` personas.

    if not personas and count > 0:
        logger.error("Failed to generate any valid personas after processing LLM response.")

    return personas 