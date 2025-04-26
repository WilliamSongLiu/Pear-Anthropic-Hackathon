from llm_selector import make_llm
from typing import Dict, List, Set
import os
import shutil

company = "openai"
model = "gpt-4o-mini"
# company = "anthropic"
# model = "claude-3-5-sonnet-latest"
llm = make_llm(company, model)

def copy_starter_to_output() -> None:
    """
    Creates a copy of the 'starter' folder in the 'output' folder.
    If the output folder already exists, it will be removed first to ensure a clean copy.
    """
    starter_dir = "starter"
    output_dir = "output"

    # Remove output directory if it exists
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    # Copy the entire starter directory to output
    shutil.copytree(starter_dir, output_dir)
    print(f"Successfully copied {starter_dir} to {output_dir}")

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
        "content": """You are an expert programmer. You receive coding tasks and complete them with high-quality, production-ready code.
        Follow these guidelines:
        1. Write clean, well-documented code
        2. Include necessary imports
        3. Follow best practices for the language/framework
        4. Consider the file's role in the larger system
        5. Do not write excessive or unnecessary code
        6. Only provide code, do not provide an explanation before or after the code"""
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

if __name__ == "__main__":
    # Define the project structure
    job_description = "Write a Crossy Road game using Three.js, React-Three-Fiber, and Vite.js"
    job_files = {
        "src/styles.css": "Global stylesheet defining base typography, layout containers, and theme variables.",
        "src/assets/models/ChickenModel.jsx": "Exports a React component that loads and returns a 3D chicken model for use in the scene.",
        "src/assets/models/CarModel.jsx": "Exports a React component that loads and returns a 3D car model for use in the scene.",
        "src/assets/models/TreeModel.jsx": "Exports a React component that loads and returns a 3D tree model for use in the scene.",
        "src/components/state/Map.jsx": "Creates and provides map-layout state (tile grid, obstacles) via React Context.",
        "src/components/state/Score.jsx": "Creates and provides player score state and an updater function via Context.",
        "src/components/state/PlayerPosition.jsx": "Creates and provides player position state and an updater function via Context.",
        "src/components/state/CarInstances.jsx": "Creates and provides the array of active car instances and methods to add/remove them via Context.",
        "src/components/logic/PlayerMovement.jsx": "Listens for keyboard/touch input and invokes the PlayerPosition updater to move the player.",
        "src/components/logic/CarMovement.jsx": "Subscribes to CarInstances state and advances each car's position on every animation frame.",
        "src/components/logic/MapGeneration.jsx": "Runs once on mount to generate the initial map layout and populates the Map context.",
        "src/components/logic/CarSpawning.jsx": "On a fixed interval, creates new car entries in CarInstances state at spawn points."
    }

    # Step 1: Copy starter folder to output
    print("Step 1: Copying starter folder to output...")
    copy_starter_to_output()

    # Step 2: Set up the folder structure in the output directory
    print("\nStep 2: Setting up folder structure...")
    # Change to output directory
    os.chdir("output")
    setup_folder_structure(job_files)

    # Step 3: Generate code for each file
    print("\nStep 3: Generating code for each file...")
    for file_path, file_description in job_files.items():
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