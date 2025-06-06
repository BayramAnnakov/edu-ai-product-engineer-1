from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize the client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# List available models
models = client.models.list()

for model in models.data:
    print(model.id)
