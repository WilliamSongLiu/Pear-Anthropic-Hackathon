from llm_selector import make_llm
from typing import Dict
import json
import os
import shutil
import subprocess
import webbrowser
import time
import requests
import socket
import concurrent.futures
import argparse
import datetime

# Configuration
COMPANY = "anthropic"
MODEL = "claude-3-7-sonnet-20250219"
LLM = make_llm(COMPANY, MODEL, temperature=0)

# Constants
STARTER_DIR = "starter"
OUTPUT_DIR_SEQUENTIAL = "output_sequential"
OUTPUT_DIR_PARALLEL = "output_parallel"
IGNORED_FILES = [
    "index.html",
    "src/App.jsx",
    "src/index.jsx"
]
# Port configuration
PORT_SEQUENTIAL = 5173
PORT_PARALLEL = 5174

# Project Structure Generation
def generate_project_structure(user_prompt: str) -> Dict:
    """
    Generates a project structure based on the user's prompt.

    Args:
        user_prompt: The user's description of the project they want to create

    Returns:
        A dictionary containing 'files' and 'descriptions' for the project structure
    """
    messages = [
        {
            "role": "system",
            "content": """You are tasked with generating a project structure and file descriptions for a React Three Fiber project based on a user's prompt. Your output should be a JSON object containing two main objects: 'files' (list of files) and 'descriptions'."""
        },
        {
            "role": "user",
            "content": f"""First, you are provided with a starter code template containing the following files:
            - index.html
            - src/App.jsx
            - src/index.jsx
            - src/styles.css
            You should include these files in your described project structure.

            Now, analyze the user's prompt to understand the project requirements. Then, follow these steps:

            1. Generate the 'files' array:
            - Create a flat list of files needed for the project.
            - Include appropriate files for the 3D scene, components, and other necessary project elements.
            - The user will ask for simple projects, so create as minimal a set of files as required to complete the project.
            - Do not create files for sprites, music, favicons, or images. Only utilize JavaScript to create 3D models using React Three Fiber.
            - Do not create unrelated files for README.md, package.json, or .gitignore.
            - Create jsx files instead of js files.
            - IMPORTANT: The structure must be flat. App.jsx is the only file that can import other files. Each leaf file must work standalone and not import additional files such as hooks or components.
            - DO NOT generate a Scene.jsx file as that is the role of App.jsx.

            2. Generate the 'descriptions' object:
            - For each file in the 'files' array, create a corresponding entry in the 'descriptions' object.
            - The key should be the file path, and the value should be a brief description of the file's purpose or contents.
            - Ensure descriptions are concise but informative, explaining the role of each file in the project.
            - If there are files requiring 3D models, describe the task as creating the 3D object from primitives, not by importing outside 3D models.
            - For leaf files, clearly specify that they must be self-contained and not import other files.

            3. Format your response as a JSON object with 'files' and 'descriptions' as its main properties.

            Your final output should be formatted as follows:

            <answer>
            {{
            "files": [
                // Your generated files array here
            ],
            "descriptions": {{
                // Your generated descriptions object here
            }}
            }}
            </answer>

            Remember to tailor the project structure and descriptions to the specific requirements mentioned in the user's prompt:

            <user_prompt>
            {user_prompt}
            </user_prompt>

            Ensure that your generated project structure and file descriptions are relevant to the user's request and follow best practices for the type of project they're asking about."""
        }
    ]

    response, _ = LLM.get_completion(messages)

    try:
        start = response.find("<answer>") + len("<answer>")
        end = response.find("</answer>")
        json_str = response[start:end].strip()
        return json.loads(json_str)
    except Exception as e:
        print(f"Error parsing response: {e}")
        return None

# File System Operations
def copy_starter_to_output(output_dir: str) -> None:
    """
    Creates a copy of the 'starter' folder in the specified output folder.
    If the output folder already exists, it will be removed first to ensure a clean copy.
    Excludes node_modules and package-lock.json, then runs npm install.

    Args:
        output_dir: The directory to copy the starter files to
    """
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    ignore_patterns = shutil.ignore_patterns('node_modules', 'package-lock.json')
    shutil.copytree(STARTER_DIR, output_dir, ignore=ignore_patterns)
    print(f"Successfully copied {STARTER_DIR} to {output_dir}")

    print("Installing dependencies...")
    with open(os.devnull, 'w') as devnull:
        subprocess.run(["npm", "install"], cwd=output_dir, check=True, stdout=devnull, stderr=devnull)
    print("Dependencies installed successfully")

def setup_folder_structure(job_files: Dict[str, str]) -> None:
    """
    Creates the folder structure and empty files specified in job_files if they don't exist.
    Preserves existing files.

    Args:
        job_files: Dictionary mapping file paths to their descriptions
    """
    for file_path, _ in job_files.items():
        dir_path = os.path.dirname(file_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                pass

# Code Generation
def _clean_generated_code(content: str) -> str:
    """
    Cleans up generated code by removing markdown code block markers.

    Args:
        content: The generated code content

    Returns:
        Cleaned code content
    """
    content = content.strip()
    if content.startswith("```"):
        first_newline = content.find("\n")
        if first_newline != -1:
            content = content[first_newline + 1:]
    if content.endswith("```"):
        content = content[:-3]
    return content.strip()

def generate_app_code(task: str, file_path: str, file_description: str, job_files: Dict[str, str]) -> None:
    """
    Generate code for the App component and write it to the specified file.

    Args:
        task: The specific coding task to implement
        file_path: Path to the file where the code should be written
        file_description: Description of this file's role in the system
        job_files: Dictionary of all files and their descriptions for context
    """
    system_message = {
        "role": "system",
        "content": """You will receive specific coding tasks and complete the implementation of individual files.
        You will be provided with the requirements for what the file does, as well as its role in the overall project.
        The project structure provided is a complete and exhaustive list of the files available. Do not assume the existance of any files beyond the provided ones.
        Only provide code, do not provide an explanation before or after the code.

        Your task will be to create the App.jsx file. App.jsx will always be the top-level controller and will render the entire project.
        As such, it is very important that you:
        1. Create the Canvas component from React Three Fiber
        2. Import all the necessary components from the other files
        3. Render these components within the Canvas
        4. Set up any necessary lighting, camera, or other scene elements

        You will have context on what those components do from their file descriptions. You get to define the abstractions that those files implement.
        Ensure that if the abstractions are implemented correctly per their file descriptions, that the App.jsx file should be able to render the entire project."""
    }

    related_files = "\n".join([f"- {path}: {desc}" for path, desc in job_files.items() if path != file_path])
    user_message = {
        "role": "user",
        "content": f"""Please write code for the following task:

        Task: {task}

        This code will go in: {file_path}
        File's role: {file_description}

        Related files in the system:
        {related_files}

        Please write the complete code for this file, including all necessary imports and setup."""
    }

    content, _ = LLM.get_completion([system_message, user_message])
    content = _clean_generated_code(content)

    with open(file_path, 'w') as f:
        f.write(content)

def generate_leaf_code(task: str, file_path: str, file_description: str, job_files: Dict[str, str]) -> None:
    """
    Generate code for a leaf node task and write it to the specified file.

    Args:
        task: The specific coding task to implement
        file_path: Path to the file where the code should be written
        file_description: Description of this file's role in the system
        job_files: Dictionary of all files and their descriptions for context
    """
    system_message = {
        "role": "system",
        "content": """You will receive specific coding tasks and complete the implementation of individual files.
        You will be provided with the requirements for what the file does, as well as its role in the overall project.
        The project structure provided is a complete and exhaustive list of the files available. Do not assume the existance of any files beyond the provided ones.
        Only provide code, do not provide an explanation before or after the code.

        IMPORTANT: You have NO access to external files such as textures, models, or images.
        You MUST build all 3D objects using only primitives (Box, Sphere, Cylinder, etc.) from React Three Fiber.
        You MUST define all materials and colors directly in your code.
        DO NOT attempt to import or load any external resources."""
    }

    related_files = "\n".join([f"- {path}: {desc}" for path, desc in job_files.items() if path != file_path])
    user_message = {
        "role": "user",
        "content": f"""Please write code for the following task:

        Task: {task}

        This code will go in: {file_path}
        File's role: {file_description}

        Related files in the system:
        {related_files}

        Please write the complete code for this file, including all necessary imports and setup.

        Remember: You have NO access to external files. Build all 3D objects using only primitives and define all materials directly in your code."""
    }

    content, _ = LLM.get_completion([system_message, user_message])
    content = _clean_generated_code(content)

    with open(file_path, 'w') as f:
        f.write(content)

# Server Management
def wait_for_server(url: str, max_attempts: int = 30, delay: int = 1) -> bool:
    """
    Wait for a server to become available by checking if it responds to HTTP requests.

    Args:
        url: The URL to check
        max_attempts: Maximum number of attempts to make
        delay: Delay between attempts in seconds

    Returns:
        True if the server is available, False otherwise
    """
    print(f"Waiting for server at {url} to start...")

    for attempt in range(max_attempts):
        try:
            response = requests.get(url, timeout=1)
            if response.status_code < 400:
                print(f"Server is ready after {attempt + 1} attempts!")
                return True
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            if attempt % 5 == 0:
                print(f"Waiting for server... (attempt {attempt + 1}/{max_attempts})")
            time.sleep(delay)

    print("Server did not start within the expected time.")
    return False

def is_port_in_use(port: int) -> bool:
    """
    Check if a port is in use.

    Args:
        port: The port number to check

    Returns:
        True if the port is in use, False otherwise
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_available_port(start_port: int, max_attempts: int = 10) -> int:
    """
    Find an available port starting from the given port.

    Args:
        start_port: The port to start checking from
        max_attempts: Maximum number of ports to check

    Returns:
        An available port number
    """
    port = start_port
    for _ in range(max_attempts):
        if not is_port_in_use(port):
            return port
        port += 1
    raise RuntimeError(f"Could not find an available port after {max_attempts} attempts")

# Main Application Generation
def generate_react_three_app(user_prompt: str, use_parallel: bool = False) -> None:
    """
    Main function to generate a complete React Three Fiber app based on the user's prompt.

    Args:
        user_prompt: The user's description of the project they want to create
        use_parallel: Whether to use parallel processing for file generation
    """
    # Start the timer
    start_time = time.time()

    print(f"Generating app based on prompt: {user_prompt}")
    print(f"Using {'parallel' if use_parallel else 'sequential'} processing")

    # Determine output directory based on processing mode
    output_dir = OUTPUT_DIR_PARALLEL if use_parallel else OUTPUT_DIR_SEQUENTIAL
    base_port = PORT_PARALLEL if use_parallel else PORT_SEQUENTIAL

    # Find an available port
    try:
        port = find_available_port(base_port)
        print(f"Using port {port} for the development server")
    except RuntimeError as e:
        print(f"Warning: {e}. Using default port {base_port}.")
        port = base_port

    # Step 1: Generate project structure
    print("\nStep 1: Generating project structure...")
    project_structure = generate_project_structure(user_prompt)
    if not project_structure:
        print("Failed to generate project structure. Exiting.")
        return

    files = project_structure.get("files", [])
    descriptions = project_structure.get("descriptions", {})

    print("\nGenerated Project Structure:")
    print("----------------------------")
    print("Files:")
    print(json.dumps(files, indent=2))
    print("\nFile Descriptions:")
    print(json.dumps(descriptions, indent=2))
    print("----------------------------")

    # Step 2: Copy starter folder to output
    print(f"\nStep 2: Copying starter folder to {output_dir}...")
    copy_starter_to_output(output_dir)

    # Step 3: Set up the folder structure in the output directory
    print("\nStep 3: Setting up folder structure...")
    os.chdir(output_dir)
    setup_folder_structure(descriptions)

    # Step 4: Generate App.jsx
    print("\nStep 4: Creating App.jsx...")
    generate_app_code(
        task="Create the App.jsx file.",
        file_path="src/App.jsx",
        file_description="Main application component that renders the Scene component and provides the overall structure for the application.",
        job_files=descriptions
    )

    # Step 5: Generate code for each file (either sequentially or in parallel)
    print(f"\nStep 5: Generating code for each file {'in parallel' if use_parallel else 'sequentially'}...")

    # Filter out ignored files
    files_to_generate = [file_path for file_path in files if file_path not in IGNORED_FILES]

    # Function to generate a single file with retry logic
    def generate_file_with_retry(file_path, max_retries=3):
        file_description = descriptions.get(file_path, "No description provided")
        print(f"\nGenerating code for {file_path}...")
        task = f"Implement the {os.path.basename(file_path)} file for the project. {file_description}"

        for attempt in range(max_retries):
            try:
                generate_leaf_code(
                    task=task,
                    file_path=file_path,
                    file_description=file_description,
                    job_files=descriptions
                )
                print(f"✓ Completed {file_path}")
                return True
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Error generating {file_path} (attempt {attempt+1}/{max_retries}): {e}")
                    print(f"Retrying in 2 seconds...")
                    time.sleep(2)
                else:
                    print(f"Failed to generate {file_path} after {max_retries} attempts: {e}")
                    return False

    if use_parallel:
        # Run all file generations in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(10, len(files_to_generate))) as executor:
            # Submit all tasks
            future_to_file = {executor.submit(generate_file_with_retry, file_path): file_path for file_path in files_to_generate}

            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    success = future.result()
                    if not success:
                        print(f"Warning: Failed to generate {file_path} after all retry attempts")
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
    else:
        # Run file generations sequentially
        for file_path in files_to_generate:
            success = generate_file_with_retry(file_path)
            if not success:
                print(f"Warning: Failed to generate {file_path} after all retry attempts")

    print("\nCode generation completed!")

    # Step 6: Start the development server
    print("\nStep 6: Starting development server...")
    print(f"Starting Vite development server on port {port}...")

    # Create a vite.config.js file with the custom port
    with open("vite.config.js", "w") as f:
        f.write(f"""import {{ defineConfig }} from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({{
  plugins: [react()],
  server: {{
    port: {port}
  }}
}})
""")

    with open(os.devnull, 'w') as devnull:
        vite_process = subprocess.Popen(["npm", "run", "dev"], stdout=devnull, stderr=devnull)

    server_url = f"http://localhost:{port}"
    if wait_for_server(server_url):
        print("Opening webpage...")
        webbrowser.open(server_url)
    else:
        print("Could not open webpage because the server did not start properly.")
        print(f"You can manually open the browser and navigate to {server_url}")

    # Calculate and print the total time taken
    end_time = time.time()
    elapsed_time = end_time - start_time
    formatted_time = str(datetime.timedelta(seconds=int(elapsed_time)))
    print(f"\nTotal time taken: {formatted_time} ({elapsed_time:.2f} seconds)")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate a React Three Fiber app based on a prompt')
    parser.add_argument('-p', '--parallel', action='store_true',
                        help='Use parallel processing for file generation')
    args = parser.parse_args()

    # Define the prompt here
    user_input = "Create a 3D office scene with a desk and monitor on it"

    generate_react_three_app(user_input, args.parallel)