import gradio as gr
from .qa import answer, summary_today
import logging
import socket
import os
import subprocess
import sys
import time

logger = logging.getLogger(__name__)

def format_chat_message(text: str, role: str = "user") -> dict:
    """Format a message for the chatbot."""
    return {"role": role, "content": text}

def kill_process_on_port(port):
    """Kill any process using the specified port."""
    try:
        if sys.platform == 'win32':
            # Windows
            result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if f':{port}' in line:
                    pid = line.strip().split()[-1]
                    subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
                    time.sleep(1)  # Wait for the process to be killed
        else:
            # Linux/Unix
            subprocess.run(['fuser', '-k', f'{port}/tcp'], capture_output=True)
            time.sleep(1)  # Wait for the process to be killed
    except Exception as e:
        logger.warning(f"Failed to kill process on port {port}: {e}")

def ensure_port_available(port):
    """Ensure the specified port is available."""
    try:
        # Try to bind to the port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', port))
            return True
    except OSError:
        # Port is in use, try to kill the process
        logger.warning(f"Port {port} is in use. Attempting to free it...")
        kill_process_on_port(port)
        time.sleep(1)  # Wait a bit before retrying
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return True
        except OSError as e:
            logger.error(f"Could not free port {port}: {e}")
            return False

def launch():
    with gr.Blocks() as demo:
        gr.Markdown("## 🗞️ AI News Chatbot")
        gr.Markdown("Chat with the latest AI news or generate a daily summary.")
        
        backend = gr.Radio(
            choices=["ollama", "groq"],
            value="ollama",
            label="LLM Backend",
            info="Choose the AI model to use"
        )

        with gr.Tab("Chat"):
            chatbox = gr.Chatbot(
                value=[],
                label="Chat History",
                height=400,
                bubble_full_width=False
            )
            with gr.Row():
                q = gr.Textbox(
                    placeholder="Ask about the latest AI news...",
                    label="Your Question",
                    scale=4
                )
                send = gr.Button("Send", scale=1)
            
            clear = gr.Button("Clear Chat")

        with gr.Tab("Daily Summary"):
            summary_out = gr.Markdown()
            gen = gr.Button("Generate Today's Summary", variant="primary")

        def _send(msg, hist, backend_choice):
            if not msg:
                return "", hist
            try:
                # Get AI response
                resp = answer(msg, backend_choice)
                
                # Add the message pair to history (user message, assistant response)
                hist = hist + [(msg, resp)]
                return "", hist
            except Exception as e:
                logger.error(f"Error in chat response: {str(e)}")
                error_msg = "Sorry, there was an error processing your request. Please try again."
                hist = hist + [(msg, error_msg)]
                return "", hist

        def _summ(backend_choice):
            try:
                return summary_today(backend_choice)
            except Exception as e:
                logger.error(f"Error generating summary: {str(e)}")
                return "Sorry, there was an error generating the summary. Please try again."

        def _clear():
            return [], ""

        # Event handlers
        send.click(
            _send,
            inputs=[q, chatbox, backend],
            outputs=[q, chatbox]
        )
        
        q.submit(
            _send,
            inputs=[q, chatbox, backend],
            outputs=[q, chatbox]
        )
        
        clear.click(
            _clear,
            outputs=[chatbox, q]
        )
        
        gen.click(
            _summ,
            inputs=backend,
            outputs=summary_out
        )

    try:
        port = 7860  # Fixed port
        if ensure_port_available(port):
            logger.info(f"Launching server on port {port}")
            demo.launch(
                share=True,  # Enable public sharing
                debug=True,
                server_name="0.0.0.0",  # Allow external connections
                server_port=port,
                show_error=True
            )
        else:
            raise OSError(f"Could not start server on port {port}. Please ensure the port is available.")
    except Exception as e:
        logger.error(f"Failed to launch server: {str(e)}")
        raise 