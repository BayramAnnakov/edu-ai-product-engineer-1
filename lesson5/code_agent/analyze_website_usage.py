"""
Analyze a web-analytics CSV with Code Interpreter,
then download every chart or file the model produces.
• Polls safely until the run is done.
• Uses the recommended container file content endpoint.
• Works with the current openai-python v1.x SDK.
"""
from dotenv import load_dotenv
load_dotenv()

import os
import time
from datetime import datetime
import openai

# ────────────── 1 · Init client ──────────────
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI()

# ────────────── 2 · Check & upload CSV ───────
csv_path = "users_analytics.csv"
if not os.path.exists(csv_path):
    raise FileNotFoundError(
        f"{csv_path} not found – please place it next to this script."
    )

print("Uploading file")

file_obj = client.files.create(
    file=open(csv_path, "rb"),
    purpose="user_data"          # fine for general analysis
)

print("Kicking off run")

# ────────────── 3 · Kick off the run ─────────
run = client.responses.create(
    model="o3",
    instructions=("""You are a senior digital-analytics consultant.
You think in hypotheses, back them with reproducible code, and separate facts from speculation.
Stay neutral; surface multiple interpretations of the data and flag uncertainty levels.

Context
An event-level CSV logs user behaviour for a website funnel:
landing_page → signup_start → signup_complete → onboarding_start → onboarding_complete → purchase
Key columns: timestamp, session_id, user_id, event, traffic_source, device_type, country, browser, experiment_variant, is_new_user.

Objectives
1. Funnel health
   • Compute overall conversion and step-by-step drop-offs (session-based)
   • Visualise as a funnel chart and a table of absolute counts & percentage rates
   • Save the funnel chart as 'funnel_chart.png'
2. Segment stress-test
   • Re-run the funnel split by traffic_source, device_type, experiment_variant
   • Highlight the 2–3 worst-performing slices and quantify the gap vs. overall
   • Save segment comparison charts as 'segment_charts.png'
3. Statistical signal check
   • Test purchase-rate differences between experiment variants (α = 0.05)
   • Flag segments with >10pp conversion gaps that are statistically significant
   • Save statistical test results as 'statistical_tests.txt'
4. Behavioural diagnostics
   • Calculate median time between steps; flag p95 > 24h steps
   • Analyze signup→onboarding drop-off and estimate revenue impact
   • Save time analysis as 'time_analysis.png'
5. Executive summary & recommendations
   • 5-bullet summary with root causes, confidence levels, impact estimates
   • 3 concrete, testable recommendations
   • Save summary as 'executive_summary.txt'

Output format
Section 1 – Plain-language insight bullets citing Section 1 numbers. Produce graphs and visualizations to accompany these insights.
Section 2 – Recommendations table (Action | Rationale | Expected lift | Priority)
Keep prose concise (≤ 4 lines per paragraph)

IMPORTANT: For each visualization or analysis, explicitly save the output to a file using appropriate methods:
- For plots: plt.savefig('filename.png')
- For tables: df.to_csv('filename.csv')
- For text: with open('filename.txt', 'w') as f: f.write(content)"""),
    tools=[{
        "type": "code_interpreter",
        "container": {
            "type": "auto",
            "file_ids": [file_obj.id]
        }
    }],
    input="Analyze website usage data, provide insights and illustrate them with graphs"
)

print(f"Run created: {run.id}")

# ────────────── 4 · Wait until finished ──────

poll_every = 2  # seconds
while run.status in ("queued", "in_progress"):
    print(f"⏳ {run.status} …")
    time.sleep(poll_every)
    run = client.responses.retrieve(run.id)

print(f"✅ Run finished with status: {run.status}")

# ────────────── 5 · Show plain-text answer ───
print("\nAnalysis results:\n")
print(run.output_text or "[No text output]")
