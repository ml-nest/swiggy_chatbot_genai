import os
import json

# importing the credentials
from dotenv import load_dotenv  
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
model_name = os.getenv("model")

# just a simple chat interface
import gradio as gr
import time

# Using Chatmodels groq API
from groq import Groq
client = Groq()

# # Importing the Azure OpenAI client
# from openai import AzureOpenAI
# api_key = os.getenv("AZURE_OPENAI_KEY")
# endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
# model = os.getenv("AZURE_OPENAI_MODEL")

# # Initialize Azure OpenAI client
# client = AzureOpenAI(
#     azure_endpoint=endpoint,
#     api_key=api_key,
#     api_version="2023-03-15-preview"
# )



# Declaring the system message for the food delivery chatbot
system_message = "You are a helpful assistant for an food delivery company.\
Give short, courteous answers, no more than 1 sentence. \
Always be accurate. If you don't know the answer or the \
information is insufficient, do not make up an answer. Ask for more \
information and simply say that you cant answer at the moment due \
to lack of information."


# Creating a chatbot with no tools, just a simple chat interface
def chat(message, history):
    
    # Dropping useless things from history variable and feeding it to the model
    history = [{'role': h['role'], 'content': h['content']} for h in history]
    
    messages = [{"role": "system", "content": system_message}] + history + [{"role": "user", "content": message}]

    stream = client.chat.completions.create(model=model_name,
                                            messages=messages,
                                            temperature=0,
                                            stream=True)
    # stream = client.chat.completions.create(
    #     model=model,
    #     messages=messages,
    #     temperature=0,
    #     stream=True)
    
    response = ""
    for chunk in stream:
        response += chunk.choices[0].delta.content or ''
        time.sleep(0.05)
        yield response

gr.ChatInterface(fn=chat, type="messages").launch()


