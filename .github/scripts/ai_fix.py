import os
from google import genai
from google.genai import types

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Skipping: No API Key found.")
        return
    log_content = "No logs found."
    if os.path.exists("failed_logs.txt"):
        with open("failed_logs.txt", "r") as f:
            log_content = f.read()
            if len(log_content) > 100000: 
                log_content = log_content[-100000:]
    repo_context = "No context found."
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
       - Remediation: Show the specific failure trace and link to lines in the code.

    **Response Format:**
    - Start with a friendly greeting to the @contributor.
    - clearly state WHAT failed.
    - Provide the "Remediation" step (command to run or code to change).
    - Use Markdown.
    """

    prompt = f"""
    Here are the logs from the failed CI run:
    <logs>
    {log_content}
    </logs>

    Here is the relevant source code context:
    <code_context>
    {repo_context}
    </code_context>

    Analyze the logs, find the root cause, and generate the GitHub comment.
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite', 
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction
            )
        )
        print(response.text)
    except Exception as e:
        print(f"AI Generation Failed: {e}")

if __name__ == "__main__":
    main()
