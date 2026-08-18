import gradio as gr

from app.ui.client import login, respond

with gr.Blocks(title="ariabot") as demo:
    access_token_box = gr.Textbox(label="Access Token", type="password")
    login_button = gr.Button("Login")
    login_status = gr.Markdown()

    login_button.click(fn=login, inputs=[], outputs=[access_token_box, login_status])

    gr.ChatInterface(fn=respond, additional_inputs=[access_token_box])
