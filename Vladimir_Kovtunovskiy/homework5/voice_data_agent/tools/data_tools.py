import csv
import json
import os
from google import genai
from google.genai import types

# Global variable to hold current CSV file path 
CSV_FILE_PATH = "voice_data_agent/data/UberDataset.csv"
OUTPUT_DIRECTORY = "voice_data_agent/visualizations"
OUTPUT_FILENAME = "uber_data_visualization.png"
CODE_MODEL = "gemini-2.5-flash-preview-04-17"

def read_csv() -> str:
    """
    Reads the entire CSV file and returns it as a JSON string.
    """
    try:
        with open(CSV_FILE_PATH, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            data = [row for row in reader]
    except Exception as e:
        return f"Error reading CSV: {e}"

    if not data:
        return "CSV file is empty."
    return json.dumps(data, indent=2)

def generate_plot(data_json: str):
    """
        This function will generate a plot for the given data.

        Args:
            data_json (str): The data to generate a plot for in json format.
    """

    prompt = f"""
        This is a data analysis agent. Your role is to generate python code to create a plot of the data.
        here is the data in json format:
        {data_json}

        Generate Python code using Matplotlib to create a line plot of this sales data.

        Execute the code and return the plot image file.
    """

    print(f"Generating plot with prompt: {prompt}")
    client = genai.Client()

    response = client.models.generate_content(
        model=CODE_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
        tools=[types.Tool(
            code_execution=types.ToolCodeExecution
            )]
        )
    )

     # Process the response parts to find text, code, and the output file
    generated_text_parts = []
    executable_code = None
    code_execution_output = None
    output_file_data = None
    output_file_mime_type = None

    if not response.candidates:
        print("🔴 No candidates found in the response.")
        return

    for part in response.candidates[0].content.parts:
        if part.text:
            generated_text_parts.append(part.text)
        elif hasattr(part, 'executable_code') and part.executable_code:
            executable_code = part.executable_code.code
        elif hasattr(part, 'code_execution_result') and part.code_execution_result:
            code_execution_output = part.code_execution_result.output
        # Check for inline_data which usually contains the generated file [3, 8]
        elif hasattr(part, 'inline_data') and part.inline_data:
            output_file_data = part.inline_data.data # This should be the image bytes
            output_file_mime_type = part.inline_data.mime_type
            print(f"✅ Found inline_data (likely the image): mime_type='{output_file_mime_type}'")
        # Fallback or alternative for file_data (structure might vary slightly with SDK updates)
        elif hasattr(part, 'file_data') and part.file_data: # [11] (though for input, good to check)
             output_file_data = part.file_data.blob # Or .data depending on exact SDK version/response
             output_file_mime_type = part.file_data.mime_type
             print(f"✅ Found file_data (likely the image): mime_type='{output_file_mime_type}'")


    if generated_text_parts:
        print("\n--- Model's Text Response ---")
        for text_part in generated_text_parts:
            print(text_part)

    if executable_code:
        print("\n--- Model's Executable Code ---")
        print(executable_code)
        if code_execution_output:
            print("\n--- Code Execution Output (stdout/stderr) ---")
            print(code_execution_output)
        else:
            print("\n--- Code was generated but no explicit execution output string was found (image output is separate). ---")


    # Save the extracted file data to the local directory
    if output_file_data:
        # Create the output directory if it doesn't exist
        if not os.path.exists(OUTPUT_DIRECTORY):
            os.makedirs(OUTPUT_DIRECTORY)
            print(f"\nCreated directory: {OUTPUT_DIRECTORY}")

        # Determine file extension based on mime type, default to .png if common image type
        file_extension = ".png" # Default
        if output_file_mime_type:
            if "png" in output_file_mime_type:
                file_extension = ".png"
            elif "jpeg" in output_file_mime_type or "jpg" in output_file_mime_type:
                file_extension = ".jpg"
            elif "svg" in output_file_mime_type:
                file_extension = ".svg"
            # Add more mime types as needed
        
        # If OUTPUT_FILENAME already has an extension, respect it, otherwise append.
        if not os.path.splitext(OUTPUT_FILENAME)[1]:
            local_file_path = os.path.join(OUTPUT_DIRECTORY, OUTPUT_FILENAME + file_extension)
        else: # If OUTPUT_FILENAME already specified an extension
            local_file_path = os.path.join(OUTPUT_DIRECTORY, OUTPUT_FILENAME)


        try:
            with open(local_file_path, "wb") as f:
                f.write(output_file_data)
            print(f"\n✅ Successfully saved visualization to: {local_file_path}")
        except IOError as e:
            print(f"🔴 Error saving the file: {e}")
    else:
        print("\n🔴 No image file data found in the model's response.")
        print("   This could be due to: ")
        print("   - The model not generating the file as requested.")
        print("   - The API response structure for files being different than expected.")
        print("   - The chosen model not supporting file output effectively for this task.") 