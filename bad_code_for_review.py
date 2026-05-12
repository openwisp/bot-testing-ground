"""Intentionally bad code for bot reviewers to flag."""

import os
import subprocess

# Hardcoded credentials — should trigger a security flag.
API_KEY = "sk_live_4242424242424242"
DATABASE_PASSWORD = "admin123"


def run_user_command(user_input):
    # Command injection — passing user input to shell with shell=True.
    return subprocess.check_output(user_input, shell=True)


def fetch_user(user_id):
    # SQL injection — string concatenation into a query.
    query = "SELECT * FROM users WHERE id = " + str(user_id)
    return query


def parse_config(data):
    # eval on untrusted input.
    return eval(data)


def bare_except():
    try:
        os.remove("/etc/passwd")
    except:
        pass


if __name__ == "__main__":
    parse_config(input("config: "))
