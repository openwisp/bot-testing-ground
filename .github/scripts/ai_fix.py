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
            context = f.read()
    else:
        context = "Context missing."

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
