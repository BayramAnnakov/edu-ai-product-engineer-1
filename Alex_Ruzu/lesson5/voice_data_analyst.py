import os
import subprocess
import pandas as pd
from dotenv import load_dotenv
import glob

from livekit import agents
from livekit.agents import Agent, AgentSession, RoomInputOptions
from livekit.plugins import (
    openai,
    noise_cancellation,
)

load_dotenv()

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "code_agent", "sandbox_output")

def analysis_outputs_exist():
    return len(glob.glob(os.path.join(OUTPUT_DIR, "*.csv"))) > 0

def run_analysis():
    subprocess.run(["python", "runner.py"], check=True, cwd="code_agent")

def load_results():
    csv_files = glob.glob(os.path.join(OUTPUT_DIR, "*.csv"))
    results = {}
    summary_strs = []
    for csv_path in csv_files:
        key = os.path.splitext(os.path.basename(csv_path))[0]
        df = pd.read_csv(csv_path)
        results[key] = df
        summary_strs.append(f"{key}:\n{df.head(10).to_string(index=False)}\n")
    results["llm_context"] = "\n".join(summary_strs)
    return results


results = None

class Assistant(Agent):
    def __init__(self, analytics_summary) -> None:
        super().__init__(
            instructions=(
                f"You are a helpful voice AI data analyst. Here is the latest analytics summary: {analytics_summary} "
                "When the user asks about analytics, answer using this data."
            )
        )

async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(voice="coral")
    )
    await session.start(
        room=ctx.room,
        agent=Assistant(load_results()["llm_context"]),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )
    await ctx.connect()
    await session.generate_reply(
        instructions="Say hello, AI Product Engineer course participants!"
    )

def main():
    global results
    if not analysis_outputs_exist():
        print("Running analysis...")
        run_analysis()
    else:
        print("Analysis results found. Loading...")
    results = load_results()
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))

if __name__ == "__main__":
    main()
