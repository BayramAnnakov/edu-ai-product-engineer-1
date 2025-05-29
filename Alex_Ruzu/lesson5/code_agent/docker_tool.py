# docker_tool.py
import os, subprocess, tempfile, shutil
from agents import function_tool
import csv_tool  # Import the entire module to access CSV_FILE_PATH

# Use a fixed output directory for charts generated in the container
OUTPUT_DIR = "sandbox_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

@function_tool
def execute_python(code: str) -> str:
    """
    Executes the given Python code string inside a sandboxed Docker container.
    Returns the combined stdout/stderr output from the code execution.
    Any files saved to /app/output/ in the code will be available in the host OUTPUT_DIR.
    """
    print("\n=== Docker Tool Execution Started ===")
    print(f"Code to execute:\n{'-'*50}\n{code}\n{'-'*50}")

    if not csv_tool.CSV_FILE_PATH:
        error_msg = "Error: CSV_FILE_PATH is not set. Please set it before running analysis."
        print(error_msg)
        return error_msg

    if not os.path.exists(csv_tool.CSV_FILE_PATH):
        error_msg = f"Error: CSV file not found at {csv_tool.CSV_FILE_PATH}"
        print(error_msg)
        return error_msg

    # Write the code to a temporary file
    temp_dir = tempfile.mkdtemp(prefix="agent_code_")
    code_path = os.path.join(temp_dir, "user_code.py")
    with open(code_path, "w") as f:
        f.write(code)
    print(f"\nTemporary code file created at: {code_path}")

    # Form the docker run command
    docker_image = "ai_sandbox"  # Image name built from Dockerfile
    container_cmd = [
        "docker", "run", "--rm",
        "--network", "none",           # no network access for security
        "--memory", "1g", "--cpus", "1",  # limit resources: 1 GB RAM, 1 CPU
        "--security-opt", "no-new-privileges",  # prevent privilege escalation
        "-v", f"{os.path.abspath(csv_tool.CSV_FILE_PATH)}:/app/data.csv:ro",        # mount CSV as read-only
        "-v", f"{os.path.abspath(OUTPUT_DIR)}:/app/output:rw",             # mount output dir for charts
        "-v", f"{code_path}:/app/user_code.py:ro",        # mount the code file
        "-w", "/app",   # working directory inside container
        docker_image, "python3", "-u", "user_code.py"
    ]
    print("\nDocker command to execute:")
    print(" ".join(container_cmd))

    try:
        print("\nExecuting Docker container...")
        result = subprocess.run(container_cmd, capture_output=True, text=True, timeout=60)
        print("\nDocker execution completed")
        print("\nDocker stdout:")
        print(result.stdout)
        if result.stderr:
            print("\nDocker stderr:")
            print(result.stderr)
    except subprocess.TimeoutExpired:
        print("\nDocker execution timed out!")
        # Kill the container if still running and return timeout message
        subprocess.run(["docker", "kill", "$(docker ps -q --filter ancestor=ai_sandbox)"], shell=True)
        shutil.rmtree(temp_dir, ignore_errors=True)
        return "Error: Code execution timed out."
    except Exception as e:
        error_msg = f"Error executing Docker container: {str(e)}"
        print(f"\n{error_msg}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return error_msg

    # Clean up the temp code file directory
    shutil.rmtree(temp_dir, ignore_errors=True)
    print("\nTemporary files cleaned up")

    # Combine stdout and stderr
    output_text = result.stdout + ("\n" + result.stderr if result.stderr else "")
    # Truncate output if very long (prevent overwhelming response)
    if len(output_text) > 10000:
        output_text = output_text[:10000] + "... [output truncated]"
    
    print("\n=== Docker Tool Execution Completed ===")
    return output_text.strip()
