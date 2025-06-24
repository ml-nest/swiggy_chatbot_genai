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


# Creating a chatbot with agents to know status of my order, just a simple chat interface, 
import datetime as dt
import pandas as pd

deliveries_df = pd.read_csv("./data/deliveries.csv")
# converting the order_id to lower case
deliveries_df['order_id'] = deliveries_df['order_id'].str.lower()
deliveries_df['status'] = deliveries_df['status'].str.lower()
deliveries_df['order_time'] = pd.to_datetime(deliveries_df['order_time'])
deliveries_df['estimate_time'] = pd.to_datetime(deliveries_df['estimate_time'])


# Defining the function that will be called by the chatbot to get the order details
order_function = {
    "name": "order_details",
    "description": "Get the status of the order the customer has placed. Call this whenever a customer asks about their order status, for example when they say 'Where is my order?'",
    "parameters": {
        "type": "object",
        "properties": {
            "order_id": {
                "type": "string",
                "description": "The ID of the order that the customer wants to check",
            },
        },
        "required": ["order_id"],
        "additionalProperties": False
    }}



def order_details(order_id, deliveries_df):
    order_id = order_id.lower()
    # Fetching the order details from the dataframe
    order = deliveries_df[deliveries_df['order_id'] == order_id]
    if order.empty:
        return "Order not found."
    else:
        status = order['status'].values[0]
        order_time = order['order_time'].values[0]
        estimate_time = order['estimate_time'].values[0]
        # subtract to datetime obects and return in minutes
        estimate_minutes = int((estimate_time - order_time) / 60000000000)
        if status == "delivered":
            return f"Your order {order_id} has been delivered on {pd.to_datetime(estimate_time)}."
        elif status == "cancelled":
            return f"Your order {order_id} has been cancelled on {pd.to_datetime(estimate_time)}."
        elif status == "in transit":
            return f"Your order {order_id} is currently {status}. It was placed on {pd.to_datetime(order_time)} and is estimated to be delivered in {estimate_minutes} minutes."

# order_id = "A101"
# order_details(order_id, deliveries_df)


# We can define the tools as a list of dictionaries, each containing a function definition
tools = [{"type": "function", "function": order_function}]


# Testing if the function calls a tool
message = 'Hello'
messages = [{"role": "system", "content": system_message}] + [{"role": "user", "content": message}]
response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0,
            tools=tools,
            tool_choice="auto")
print(response)

messages = messages + [{"role": "user", "content": "Where's my order?"}]
response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0,
            tools=tools,
            tool_choice="auto")
print(response)

messages = messages + [{"role": "user", "content": "Order ID is 12345"}]
response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0,
            tools=tools,
            tool_choice="auto")
print(response) #it does - Reason for completion is tool_calls




# We have to write a function that will handle the tool call and return the response
def handle_tool_call(message):
    tool_call = message.tool_calls[0]
    arguments = json.loads(tool_call.function.arguments)
    order_id = arguments.get('order_id')
    comment = order_details(order_id ,deliveries_df)
    response = {
        "role": "tool",
        "content": json.dumps({"order_id": order_id,"answer": comment}),
        "tool_call_id": message.tool_calls[0].id
    }
    return response, order_id



# Now we can create a chatbot that uses the tool to get the order detail
# Order information
def chat(message, history):
    history = [{'role': h['role'], 'content': h['content']} for h in history]
    messages = [{"role": "system", "content": system_message}] + history + [{"role": "user", "content": message}]
    
    
    response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0,
            tools=tools,
            tool_choice="auto")
    
    # If the response contains a tool call, we handle it
    if response.choices[0].finish_reason=="tool_calls":
        message = response.choices[0].message
        response, order_id = handle_tool_call(message)
        messages.append(message)
        messages.append(response)
        # response = client.chat.completions.create(model="llama3-8b-8192",
        #         temperature=0,
        #         messages=messages)
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0)
    return response.choices[0].message.content


gr.ChatInterface(fn=chat, type="messages").launch()