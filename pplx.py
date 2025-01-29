from openai import OpenAI
import os
from datetime import datetime
import re

from dotenv import load_dotenv
load_dotenv()
YOUR_API_KEY = os.getenv("PPLX_API_KEY")

def read_prompt(filename):
    with open(filename, 'r') as f:
        return f.read().strip()

def generate_filename(user_prompt):
    # Extract first few words from the prompt (limit to 5 words)
    first_words = ' '.join(user_prompt.split()[:5]).lower()
    # Remove special characters and replace spaces with underscores
    topic = re.sub(r'[^a-z0-9\s]', '', first_words)
    topic = re.sub(r'\s+', '_', topic.strip())
    # Add timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Create conversations directory if it doesn't exist
    os.makedirs('conversations', exist_ok=True)
    return f"conversations/{topic}_{timestamp}.md"

def write_output(filename, system_prompt, user_prompt, response_content):
    # Write to conversation file
    with open(filename, 'w') as f:
        f.write("# Conversation\n\n")
        f.write("## System Prompt\n")
        f.write(f"{system_prompt}\n\n")
        f.write("## Conversation History\n\n")
        
        f.write("### User\n")
        f.write(f"{user_prompt}\n\n")
        f.write("### Assistant\n")
        f.write(f"{response_content}\n\n")
        
        f.write("<!-- Continue conversation below this line -->\n")

    # Update user_prompt.md with the conversation history
    with open('prompts/user_prompt.md', 'w') as f:
        f.write("# Previous Conversation\n\n")
        f.write("### User\n")
        f.write(f"{user_prompt}\n\n")
        f.write("### Assistant\n")
        f.write(f"{response_content}\n\n")
        f.write("# New Message\n")
        f.write("<!-- Write your new message here -->\n")

def main():
    # Read prompts from files
    system_prompt = read_prompt('prompts/system_prompt.md')
    user_prompt = read_prompt('prompts/user_prompt.md')

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_prompt
        }
    ]

    client = OpenAI(api_key=YOUR_API_KEY, base_url="https://api.perplexity.ai")

    # Generate filename based on prompt content
    output_filename = generate_filename(user_prompt)

    # Get response
    response = client.chat.completions.create(
        model="sonar-pro",
        messages=messages,
    )

    # Write output to file
    write_output(
        output_filename,
        system_prompt,
        user_prompt,
        response.choices[0].message.content
    )

if __name__ == "__main__":
    main()
