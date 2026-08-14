import gradio as gr

from app.ui.client import respond

demo = gr.ChatInterface(fn=respond, title="ariabot")
