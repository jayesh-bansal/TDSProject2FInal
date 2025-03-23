import re
import httpx
import os

BASE_URL = "https://aiproxy.sanand.workers.dev/openai/v1"


def GA3_1(question):
    match = re.search(r"meaningless text:\s*(.*?)\s*Write a",
                      question, re.DOTALL)

    if not match:
        return "Error: No match found in the input string."

    meaningless_text = match.group(1).strip()

    python_code = f"""
import httpx
model = "gpt-4o-mini"
messages = [
    {{"role": "system", "content": "LLM Analyze the sentiment of the text. Make sure you mention GOOD, BAD, or NEUTRAL as the categories."}}, 
    {{"role": "user", "content": "{meaningless_text}"}}
]
data = {{"model": model,"messages": messages}}
headers = {{"Content-Type": "application/json","Authorization": "Bearer dummy_api_key"}}
response = httpx.post("https://api.openai.com/v1/chat/completions", json=data, headers=headers)
print(response.json())"""
    return python_code

# question="""
# DataSentinel Inc. is a tech company specializing in building advanced natural language processing (NLP) solutions. Their latest project involves integrating an AI-powered sentiment analysis module into an internal monitoring dashboard. The goal is to automatically classify large volumes of unstructured feedback and text data from various sources as either GOOD, BAD, or NEUTRAL. As part of the quality assurance process, the development team needs to test the integration with a series of sample inputs—even ones that may not represent coherent text—to ensure that the system routes and processes the data correctly.

# Before rolling out the live system, the team creates a test harness using Python. The harness employs the httpx library to send POST requests to OpenAI's API. For this proof-of-concept, the team uses the dummy model gpt-4o-mini along with a dummy API key in the Authorization header to simulate real API calls.

# One of the test cases involves sending a sample piece of meaningless text:

# d4A aWl1FbqmD9 j SEIWdsMNo Jw e8cRbq  v  WCu WQL K
# Write a Python program that uses httpx to send a POST request to OpenAI's API to analyze the sentiment of this (meaningless) text into GOOD, BAD or NEUTRAL. Specifically:

# Make sure you pass an Authorization header with dummy API key.
# Use gpt-4o-mini as the model.
# The first message must be a system message asking the LLM to analyze the sentiment of the text. Make sure you mention GOOD, BAD, or NEUTRAL as the categories.
# The second message must be exactly the text contained above.
# This test is crucial for DataSentinel Inc. as it validates both the API integration and the correctness of message formatting in a controlled environment. Once verified, the same mechanism will be used to process genuine customer feedback, ensuring that the sentiment analysis module reliably categorizes data as GOOD, BAD, or NEUTRAL. This reliability is essential for maintaining high operational standards and swift response times in real-world applications.

# Note: This uses a dummy httpx library, not the real one. You can only use:

# response = httpx.get(url, **kwargs)
# response = httpx.post(url, json=None, **kwargs)
# response.raise_for_status()
# response.json()
# Code
# """
# print(GA3_1(question))


def GA3_2(question):
    match = re.search(
        r"List only the valid English words from these:(.*?)\s*\.\.\. how many input tokens does it use up?",
        question, re.DOTALL
    )
    if not match:
        return "Error: No valid input found."
    user_message = "List only the valid English words from these: " + \
        match.group(1).strip()
    # Make a real request to get the accurate token count
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": user_message}]
    }
    API_KEY = os.getenv("AIPROXY_TOKEN")  # Set this variable in your system
    print(API_KEY)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    response = httpx.post(BASE_URL + "/chat/completions",
                          json=data, headers=headers)

    return response.json().get("usage", {}).get("prompt_tokens")


# question="""
# Specifically, when you make a request to OpenAI's GPT-4o-Mini with just this user message:

# List only the valid English words from these: 4CyRh5aMGr, YfH9DFZeI, rmNyoh6u, k, 6IdO, OC
# ... how many input tokens does it use up?
# """
# print(GA3_2(question))
