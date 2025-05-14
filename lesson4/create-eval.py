from dotenv import load_dotenv

load_dotenv()

import openai, os, json
from schemas import ReviewRow
from graders import (
    bug_feature_grader,
    feature_quality_grader,
)

openai.api_key = os.environ["OPENAI_API_KEY"]

data_source_config = {
    "type": "custom",
    "item_schema": ReviewRow.model_json_schema(),  # JSON-Schema export
    "include_sample_schema": True,                 # exposes {{sample.output_text}}
}

eval_create_response = openai.evals.create(
    name="ai-pm-agent-eval",
    metadata={
        "description": "Checks classification, deduplication and proposal quality "
                       "for the AI Product-Manager agent",
    },
    data_source_config=data_source_config,
    testing_criteria=[
        bug_feature_grader,
        feature_quality_grader,
    ],
)

EVAL_ID = eval_create_response.id
print("Eval created:", EVAL_ID)
