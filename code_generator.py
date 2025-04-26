from llm_selector import make_llm
from typing import Dict
import os
import shutil
import subprocess
import webbrowser

# company = "openai"
# model = "gpt-4o-mini"
company = "anthropic"
model = "claude-3-5-haiku-latest"
llm = make_llm(company, model)

def copy_starter_to_output() -> None:
    """
    Creates a copy of the 'starter' folder in the 'output' folder.
    If the output folder already exists, it will be removed first to ensure a clean copy.
    Excludes node_modules and package-lock.json, then runs npm install.
    """
    starter_dir = "starter"
    output_dir = "output"

    # Remove output directory if it exists
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    # Define what to ignore during copy
    ignore_patterns = shutil.ignore_patterns('node_modules', 'package-lock.json')

    # Copy the starter directory to output, excluding specified files/directories
    shutil.copytree(starter_dir, output_dir, ignore=ignore_patterns)
    print(f"Successfully copied {starter_dir} to {output_dir}")

    # Run npm install in the output directory
    print("Installing dependencies...")
    subprocess.run(["npm", "install"], cwd=output_dir, check=True)
    print("Dependencies installed successfully")

def setup_folder_structure(job_files: Dict[str, str]) -> None:
    """
    Creates the folder structure and empty files specified in job_files if they don't exist.
    Preserves existing files.

    Args:
        job_files: Dictionary mapping file paths to their descriptions
    """
    for file_path, _ in job_files.items():
        # Get the directory path
        dir_path = os.path.dirname(file_path)

        # Create directories if they don't exist
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)

        # Create file if it doesn't exist
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                pass  # Create empty file

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
        As such, it is very important that you import all the necessary components and render them. You will have context on what those components 
        from their file descriptions. You get to define the abstractions that those files implement. Ensure that if the abstractions
        are implemented correctly per their file descriptions, that the App.jsx file should be able to render the entire project. As such, app.jsx
        should have very little code in it and can just utilize the components implemented by the other jobs."""
    }

    # Create context about the file's role and related files
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

    messages = [system_message, user_message]
    content, _ = llm.get_completion(messages)

    # Clean up the generated code by removing markdown code block markers
    content = content.strip()
    if content.startswith("```"):
        # Find the first newline after the opening ```
        first_newline = content.find("\n")
        if first_newline != -1:
            content = content[first_newline + 1:]

    if content.endswith("```"):
        # Remove the closing ```
        content = content[:-3]

    content = content.strip()

    # Write the cleaned code to the file
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
    # Read App.jsx code to provide interface for leaf components
    try:
        with open('src/App.jsx', 'r') as f:
            app_code = f.read()
    except FileNotFoundError:
        app_code = ""

    system_message = {
        "role": "system",
        "content": """You will receive specific coding tasks and complete the implementation of individual files.
        You will be provided with the requirements for what the file does, as well as its role in the overall project.
        The project structure provided is a complete and exhaustive list of the files available. Do not assume the existence of any files beyond the provided ones.
        Additionally, you have access to the App.jsx code which defines how your component will be used. Please ensure your implementation conforms to the interface as invoked by App.jsx.
        Only provide code, do not provide an explanation before or after the code."""
    }

    # Create context about the file's role and related files
    related_files = "\n".join([f"- {path}: {desc}" for path, desc in job_files.items() if path != file_path])

    user_message = {
        "role": "user",
        "content": f"""Please write code for the following task:

Task: {task}

This code will go in: {file_path}
File's role: {file_description}

Related files in the system:
{related_files}

App.jsx code:
```jsx
{app_code}
```

Please write the complete code for this file, including all necessary imports and setup."""
    }

    messages = [system_message, user_message]
    content, _ = llm.get_completion(messages)

    # Clean up the generated code by removing markdown code block markers
    content = content.strip()
    if content.startswith("```"):
        # Find the first newline after the opening ```
        first_newline = content.find("\n")
        if first_newline != -1:
            content = content[first_newline + 1:]

    if content.endswith("```"):
        # Remove the closing ```
        content = content[:-3]

    content = content.strip()

    # Write the cleaned code to the file
    with open(file_path, 'w') as f:
        f.write(content)

if __name__ == "__main__":
    # Define the project structure
    job_description = "Create a spinning 3D cube using Three.js, React-Three-Fiber, and Vite.js"

    # Files to skip during generation (these should already exist in the starter template)
    ignored_files = [
        "src/App.jsx",
        "src/index.jsx"
    ]

    job_files = {
        "src/components/Cube.jsx": "Defines the 3D cube component using React Three Fiber. Implements the cube geometry with materials and rotation animation.",
        "src/components/Scene.jsx": "Sets up the 3D scene with camera, lighting, and environment. Contains the Canvas component from React Three Fiber and imports the Cube component.",
        "src/App.jsx": "Main application component that renders the Scene component and provides the overall structure for the application.",
        "src/index.jsx": "Entry point of the application. Renders the App component to the DOM and sets up React.",
        "src/styles.css": "Contains CSS styles for the application, including canvas sizing and any UI elements."
    }

    # Step 1: Copy starter folder to output
    print("Step 1: Copying starter folder to output...")
    copy_starter_to_output()

    # Step 2: Set up the folder structure in the output directory
    print("\nStep 2: Setting up folder structure...")
    # Change to output directory
    os.chdir("output")
    setup_folder_structure(job_files)

    # Step 2.5: Create App.jsx
    print("\nStep 2.5: Creating App.jsx...")
    generate_app_code(
        task="Create the App.jsx file for the 3D cube application.",
        file_path="src/App.jsx",
        file_description="Main application component that renders the Scene component and provides the overall structure for the application.",
        job_files=job_files
    )

    # Step 3: Generate code for each file
    print("\nStep 3: Generating code for each file...")
    for file_path, file_description in job_files.items():
        if file_path in ignored_files:
            print(f"\nSkipping {file_path} (in ignored files list)...")
            continue

        print(f"\nGenerating code for {file_path}...")
        task = f"Implement the {os.path.basename(file_path)} file for the Crossy Road game. {file_description}"
        generate_leaf_code(
            task=task,
            file_path=file_path,
            file_description=file_description,
            job_files=job_files
        )
        print(f"✓ Completed {file_path}")

    print("\nCode generation completed successfully!")

    # Step 4: Install dependencies and start the development server
    print("\nStep 4: Starting development server...")

    # Start the development server in the background
    print("Starting Vite development server...")
    vite_process = subprocess.Popen(["npm", "run", "dev"])

    # Open the webpage in the default browser
    print("Opening webpage...")
    webbrowser.open("http://localhost:5173")