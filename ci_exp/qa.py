import subprocess
import sys
import shutil

TARGET = "file.py"  

def run_command(command, name):
    if not shutil.which(command.split()[0]):
        print(f" Error: '{name}' tool is missing.")
        print(f" Fix: pip install {name}")
        return False

    print(f" Checking {name} on {TARGET}...")
    result = subprocess.run(
        command, 
        shell=True, 
        capture_output=True, 
        text=True
    )
    
    if result.returncode != 0:
        print(f" {name} FAILED!")
        print(f"   Reason:\n{result.stderr or result.stdout}")
        return False
    else:
        print(f" {name} passed!")
        return True

def main():
    print(f" Running QA on: {TARGET}\n")
    
    checks = [
        (f"black --check {TARGET}", "black"), 
        (f"flake8 {TARGET}", "flake8"),       
    ]

    failed = False
    for cmd, tool_name in checks:
        if not run_command(cmd, tool_name):
            failed = True

    if failed:
        print("\n QA FAILED. Fix the issues above.")
        sys.exit(1)
    else:
        print("\n ALL CHECKS PASSED!")
        sys.exit(0)

if __name__ == "__main__":
    main()
