from llm_anthropic import AnthropicLLM
import json

def generate_project_structure(user_prompt):
    # Initialize the Claude model
    llm = AnthropicLLM(model="claude-3-7-sonnet-20250219", temperature=0)
    
    # Construct the system and user messages
    messages = [
        {
            "role": "system",
            "content": """You are tasked with generating a project structure and file descriptions for a web development project based on a user's prompt. Your output should be a JSON object containing two main objects: 'deps' (dependencies) and 'descriptions'."""
        },
        {
            "role": "user",
            "content": f"""First, analyze the user's prompt to understand the project requirements. Then, follow these steps:

1. Generate the 'deps' object:
   - Create a hierarchical structure representing the project's file and folder organization.
   - Start with the root folder and include common files like 'index.html'.
   - Create a 'src' folder for the main source code.
   - Include appropriate subfolders for assets, components, and other necessary project elements.
   - List individual files within each folder.
   - Represent the structure as nested objects, where each key is a file or folder name, and the value is an array of its contents (empty array for files).
   - The user will ask for simple projects, so create as minimal of a dependency graph as required to complete the project.
   - Do not create files for sprites, music, favicons, or images. Only utilize javascript files to create 3D models using React Three Fiber.
   - Do not create files for README.md, package.json, or index.html.

2. Generate the 'descriptions' object:
   - For each file in the 'deps' object, create a corresponding entry in the 'descriptions' object.
   - The key should be the file path, and the value should be a brief description of the file's purpose or contents.
   - Ensure descriptions are concise but informative, explaining the role of each file in the project.
   - If there are files requiring 3D models, describe the task as creating the 3D object from primitives, not by importing outside 3D models

3. Format your response as a JSON object with 'deps' and 'descriptions' as its main properties.

Your final output should be formatted as follows:

<answer>
{{
  "deps": {{
    // Your generated deps object here
  }},
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
    
    # Get completion from Claude
    response, _ = llm.get_completion(messages)
    
    # Extract JSON from the response
    try:
        # Find the JSON content between <answer> tags
        start = response.find("<answer>") + len("<answer>")
        end = response.find("</answer>")
        json_str = response[start:end].strip()
        
        # Parse and return the JSON
        return json.loads(json_str)
    except Exception as e:
        print(f"Error parsing response: {e}")
        return None

if __name__ == "__main__":
    # Example usage
    user_input = "Create a 3D spinning cube using React Three Fiber"
    result = generate_project_structure(user_input)
    
    if result:
        print(json.dumps(result, indent=2))
    else:
        print("Failed to generate project structure")
