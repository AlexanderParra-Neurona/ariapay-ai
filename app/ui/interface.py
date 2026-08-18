import gradio as gr

from app.ui.client import respond

demo = gr.ChatInterface(
    fn=respond,
    title="ariabot",
    additional_inputs=[gr.Textbox(label="Access Token", type="password")],
)
