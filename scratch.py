import os
from dotenv import load_dotenv
import google.generativeai as genai
import json

load_dotenv()
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash-latest")

prompt = "You are an expert AI software engineer. Analyze the following pytest failure log and the provided codebase to identify the root cause of the test failure.\n"
prompt += "Respond ONLY with a valid JSON object. Do not use markdown formatting.\n"
prompt += 'The JSON object must exactly have these string fields: "identified_error" (concise human-readable explanation), "root_cause" (logical error pinpointing), "severity" ("HIGH", "MEDIUM", "LOW"), and "recommended_fix" (how to fix it).\n\n'

test_log = "Test runner crash: TOOL_EVIDENCE_INVALID: 'NoneType' object has no attribute 'record'"
code_contents = "print('hello world')"

prompt += "--- PYTEST LOG ---\n" + test_log[:50000] + "\n\n"
prompt += "--- CODEBASE ---\n" + code_contents

response = model.generate_content(prompt)
print("RAW TEXT:")
print(response.text)
