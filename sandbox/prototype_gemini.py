"""
This is a little sandbox script to test out the Gemini API.
"""

import argparse
from decouple import config
import google.generativeai as genai

genai.configure(api_key=config("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")


def generate_a_story():
    response = model.generate_content("Write a story about a magic backpack.")
    print(response.text)


def request_code():
    response = model.generate_content(
        "Write a Python function to calculate the Fibonacci sequence."
    )
    print(response.text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gemini API prototype script")
    parser.add_argument(
        "action",
        choices=["story", "code"],
        help="Action to perform: generate a story or request code",
    )

    args = parser.parse_args()

    if args.action == "story":
        generate_a_story()
    elif args.action == "code":
        request_code()
