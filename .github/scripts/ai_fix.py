import os
import xml.etree.ElementTree as ET
from google import genai

def get_error():
    try:
        tree = ET.parse("report.xml")
        root = tree.getroot()
        for issue in root.iter():
            if issue.tag in ['failure', 'error']:
                return issue.text
    except:
        return "Log parsing failed."
    return "No error found."

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Skipping: No API Key found.")
        return
    client = genai.Client(api_key=api_key)
    error_log = get_error() 
    if os.path.exists("repo_context.xml"):
        with open("repo_context.xml", "r") as f:
            repo_context = f.read()

    client = genai.Client(api_key=api_key)
    system_instruction = """

    You are an automated CI Triage Bot for the OpenWISP project. 
    Your goal is to analyze CI failure logs and provide helpful, actionable feedback to contributors.

    Categorize the failure into one of these types:
    1. **Code Style/QA**: (flake8, isort, black, csslint, jslint).
       - Remediation: Explain the issue and tell them to run `openwisp-qa-format`.
    2. **Commit Message**: (checkcommit, conventional commits).
       - Remediation: Propose a correct commit message based on the code changes.
    3. **Test Failure**: (pytest, logic errors).
       - Remediation: Carefully compare the function logic and the test assertion. 
       - If the function logic matches its name but the test assertion is mathematically impossible, tell the contributor to fix the test.
       - If the function logic is wrong, tell them to fix the code.

    **Response Format:**
    - Start with a friendly greeting.
    - clearly state WHAT failed.
    - Provide the "Remediation" step (command to run or code to change).
    - Use Markdown.
    """

    prompt = f"""
    Fix this failing test.
    ERROR: {error_log}
    CODE: {context}
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite', 
            contents=prompt
        )
        print(f"## AI Fix\n\n{response.text}")
    except Exception as e:
        print(f"AI Generation Failed: {e}")

if __name__ == "__main__":
    main()
