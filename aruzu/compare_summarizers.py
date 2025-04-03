from openai import OpenAI
import os
from dotenv import load_dotenv

def generate_comparison_report(extractive: str, abstractive: str) -> str:
    """Generate a detailed comparison report between two summaries."""
    try:
        load_dotenv()
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert in text analysis and summarization."},
                {"role": "user", "content": f"""Compare these two summaries and provide a detailed analysis:
                
                Extractive Summary:
                {extractive}
                
                Abstractive Summary:
                {abstractive}
                
                Please analyze:
                1. Length and conciseness
                2. Key information coverage
                3. Readability and flow
                4. Overall effectiveness
                """}
            ]
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating comparison report: {str(e)}" 