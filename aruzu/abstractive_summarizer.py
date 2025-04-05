from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def abstractive_summarize(text, max_length=150):
    """
    Generate an abstractive summary using OpenAI's GPT model.
    This approach creates a new, more concise version of the text.
    """
    try:

        openai = OpenAI()
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates concise, clear summaries of text. Focus on the main ideas and key points."},
                {"role": "user", "content": f"Please summarize the following text in {max_length} words or less:\n\n{text}"}
            ],
            temperature=0.1,
            max_tokens=200
        )
        
        summary = response.choices[0].message.content.strip()
        return summary
    
    except Exception as e:
        return f"Error generating summary: {str(e)}"

if __name__ == "__main__":
    # Example usage
    text = """
    There's a lot of chatter in the media that software developers will soon lose their jobs to AI. 
    I don't buy it. It is not the end of programming. It is the end of programming as we know it today. 
    That is not new. The first programmers connected physical circuits to perform each calculation. 
    They were succeeded by programmers writing machine instructions as binary code to be input one bit at a time 
    by flipping switches on the front of a computer. Assembly language programming then put an end to that. 
    It lets a programmer use a human-like language to tell the computer to move data to locations in memory 
    and perform calculations on it. Then, development of even higher-level compiled languages like Fortran, 
    COBOL, and their successors C, C++, and Java meant that most programmers no longer wrote assembly code. 
    Instead, they could express their wishes to the computer using higher level abstractions.
    """
    
    summary = abstractive_summarize(text, max_length=100)
    print("Abstractive Summary:")
    print(summary) 