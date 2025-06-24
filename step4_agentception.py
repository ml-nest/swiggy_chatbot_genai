# In this script I'll be creating a chatbot that has multiple agents interacting with each other.

import os
import json
# importing the credentials
from dotenv import load_dotenv  
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
model_name = os.getenv("model")

# Importing the Azure OpenAI client
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

# Using Chatmodels groq API
from groq import Groq
client = Groq()


# Declaring the system message for the food delivery chatbot

system_message = "You are a helpful assistant for an food delivery company.\
Give short, courteous answers, no more than 1 sentence. \
Always be accurate. If you don't know the answer or the \
information is insufficient, do not make up an answer. Ask for more \
information and simply say that you cant answer at the moment due \
to lack of information."


# Creating a chatbot with no tools, just a simple chat interface
import gradio as gr
import time
import datetime as dt
import pandas as pd


# Creating a chatbot with agents to know status of my order, just a simple chat interface, 
import datetime as dt
import pandas as pd

deliveries_df = pd.read_csv("./data/deliveries.csv")
# converting the order_id to lower case
deliveries_df['order_id'] = deliveries_df['order_id'].str.lower()
deliveries_df['status'] = deliveries_df['status'].str.lower()
deliveries_df['order_time'] = pd.to_datetime(deliveries_df['order_time'])
deliveries_df['estimate_time'] = pd.to_datetime(deliveries_df['estimate_time'])

# Expanded food menu data
menu_data = {
    'ItemID': list(range(101, 121)),
    'ItemName': [
        'Margherita Pizza', 'Pepperoni Pizza', 'BBQ Chicken Pizza', 'Veggie Burger', 'Chicken Burger',
        'Paneer Wrap', 'Veggie Wrap', 'Chicken Caesar Wrap', 'French Fries', 'Cheese Garlic Bread',
        'Caesar Salad', 'Greek Salad', 'Cold Coffee', 'Mango Smoothie', 'Chocolate Shake',
        'Vanilla Ice Cream', 'Brownie Sundae', 'Gulab Jamun', 'Coke', 'Sprite'
    ],
    'Category': [
        'Pizza', 'Pizza', 'Pizza', 'Burger', 'Burger',
        'Wrap', 'Wrap', 'Wrap', 'Sides', 'Sides',
        'Salad', 'Salad', 'Beverage', 'Beverage', 'Beverage',
        'Dessert', 'Dessert', 'Dessert', 'Beverage', 'Beverage'
    ],
    'Price': [
        299, 349, 399, 229, 249,
        199, 189, 239, 99, 129,
        179, 189, 149, 179, 149,
        99, 159, 79, 49, 49
    ],
}


menu_function = {
    "name": "show_menu",
    "description": "LLM that displays the menu items available for ordering food. Call this whenever a customer asks to see the menu or order food.",
    "parameters": {
        "type": "object",
        "properties": {
            "new_messages": {
                "type": "string",
                "description": "Message history of the conversation with the user. This will be used to display the menu items and take orders.",
            },
        },
        "required": ["new_messages"],
        "additionalProperties": False
    }}


def show_menu(sub_history):
    # chatbot that goes through the menu items and displays them, take order from the user and calculate the final price
    system_message_2 = (
        "You are a chatbot that goes through the menu items and displays them, "
        "takes orders from the user, and calculates the final price. "
        "You can ask them to chose the category of food they want to order, "
        "and then display the items in that category. "
        "Here is the menu data:\n"
        f"{pd.DataFrame(menu_data).to_string(index=False)}"
    )
    messages = [{"role": "system", "content": system_message_2}] + sub_history 
  
    stream = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0)
    return stream



# Developing a chatbot that can also cancel an order

# Cancelling an order

# Defining the function that will be called by the chatbot to get the order details
cancel_order_function = { 
    "name": "cancel_order",
    "description": "Cancel the order the customer has placed. Call this whenever a customer asks to cancel their order, for example when they say 'I want to cancel my order'",
    "parameters": {
        "type": "object",
        "properties": {
            "order_id": {
                "type": "string",
                "description": "The ID of the order that the customer wants to cancel",
            },
        },
        "required": ["order_id"],
        "additionalProperties": False
    }}



def cancel_order(order_id, deliveries_df):
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
        if status == "cancelled":
            return f"Your order {order_id} has already been cancelled on {pd.to_datetime(estimate_time)}."
        elif status == "delivered":
            return f"Your order {order_id} has already been delivered on {pd.to_datetime(estimate_time)}. You cannot cancel it now."
        else:
            deliveries_df.loc[deliveries_df['order_id'] == order_id, 'status'] = 'cancelled'
            deliveries_df.loc[deliveries_df['order_id'] == order_id, 'estimate_time'] = dt.datetime.now()
            deliveries_df.to_csv("./data/deliveries.csv", index=False)
            return f"Your order {order_id} has been cancelled on {pd.to_datetime(dt.datetime.now())}."



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



# We can define the tools as a list of dictionaries, each containing a function definition
tools = [
    {"type": "function", "function": order_function},
    {"type": "function", "function": cancel_order_function},
    {"type": "function", "function": menu_function}
]



# Testing if the function calls a tool

messages = [{"role": "system", "content": system_message}] 

def main_food_chatbot(messages):
    while True:
        new_messages = input("👤 You: ")
        messages = messages + [{"role": "user", "content": new_messages}]
        response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=0,
                    tools=tools,
                    tool_choice="auto")
        print(response.choices[0].message.content)
        if response.choices[0].finish_reason!="tool_calls":
            messages = messages + [{"role": "assistant", "content": response.choices[0].message.content}]
        
        
        if response.choices[0].finish_reason=="tool_calls":
            message = response.choices[0].message
            tool_call = message.tool_calls[0]
            tool_name = tool_call.function.name
            if tool_name == "show_menu":
                print('we are entering the show_menu function')
                arguments = json.loads(tool_call.function.arguments)
                sub_history = [{"role": "user", "content": arguments.get('new_messages')}]
                while True:
                    comment = show_menu(sub_history)
                    print(comment.choices[0].message.content)
                    sub_history.append({"role": "assistant", "content": comment.choices[0].message.content})
                    new_messages = input("👤 You: ")
                    sub_history = sub_history + [{"role": "user", "content": new_messages}]
                    if any(phrase in new_messages.lower() for phrase in ["done", "that's all","thats all" "no more", "complete", "checkout", "thanks", "thank you"]):
                        # Add summary prompt
                        sub_history = sub_history + [{"role": "user", "content": "Please summarize my order and total bill."}]
                        comment = show_menu(sub_history)
                        print(comment.choices[0].message.content)
                        messages = messages + [{"role": "assistant", "content": comment.choices[0].message.content}]
                        break
            if tool_name == 'cancel_order':
                print('we are entering the cancel order function')
                arguments = json.loads(tool_call.function.arguments)
                order_id = arguments.get('order_id')
                # If the tool call is for cancelling an order, we call the cancel_order function
                comment = cancel_order(order_id ,deliveries_df)
                response = {
                    "role": "tool",
                    "content": json.dumps({"order_id": order_id,"answer": comment}),
                    "tool_call_id": message.tool_calls[0].id
                }
                messages.append(message)
                messages.append(response)
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=0)
                print(response.choices[0].message.content)
                
            if tool_name == "order_details":
                print('we are entering the order details function')
                # If the tool call is for order details, we call the order_details function
                arguments = json.loads(tool_call.function.arguments)
                order_id = arguments.get('order_id')
                comment = order_details(order_id ,deliveries_df)
                response = {
                    "role": "tool",
                    "content": json.dumps({"order_id": order_id,"answer": comment}),
                    "tool_call_id": message.tool_calls[0].id
                }
                messages.append(message)
                messages.append(response)
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=0)
                print(response.choices[0].message.content)



if __name__ == "__main__":
    main_food_chatbot(messages)