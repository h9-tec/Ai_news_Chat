import gradio as gr
from .qa import answer, summary_today
import logging
import socket
import os
import subprocess
import sys
import time
from .tool_agent import search_with_agent
import re
from sqlalchemy.orm import Session
from .models import Subscriber

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
    with gr.Blocks(css="""
        .tool-result {
            border: 1px solid #333;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 12px;
            background-color: #23272f;
        }
        .tool-title {
            font-weight: bold;
            margin-bottom: 5px;
            font-size: 18px;
        }
        .tool-description {
            margin: 8px 0;
        }
        .tool-tags {
            font-size: 14px;
            color: #666;
            margin-top: 8px;
        }
    """) as demo:
        gr.Markdown("# 🤖📰 AI News Chatbot")
        gr.Markdown("Chat with the latest AI news or generate a daily summary.")
        
        backend = gr.Radio(
            choices=["ollama", "groq"],
            value="groq",  # Change default to groq for better performance
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

        with gr.Tab("Tool Search"):
            tool_query = gr.Textbox(
                placeholder="Search for AI tools (e.g. video editing, image generation)",
                label="Tool Search Query",
                scale=4
            )
            num_results = gr.Dropdown(
                choices=["5", "10", "20", "50", "All"],
                value="5",
                label="Number of Results",
                scale=1
            )
            with gr.Row():
                tool_search_btn = gr.Button("Search Tools", scale=1, variant="primary")
                clear_tools_btn = gr.Button("Clear Results", scale=1)
            
            # Add a status message to show when search is in progress
            tool_status = gr.Markdown("Enter a search term above and click 'Search Tools'")
            
            # Use HTML for better formatted results
            tool_results = gr.HTML()

        with gr.Tab("Subscribe"):
            gr.Markdown("## Subscribe to Daily AI News Summary")
            email_input = gr.Textbox(
                placeholder="Enter your email address",
                label="Email Address",
                scale=4
            )
            with gr.Row():
                subscribe_btn = gr.Button("Subscribe", variant="primary")
                unsubscribe_btn = gr.Button("Unsubscribe")
            subscription_status = gr.Markdown("")

        def is_valid_email(email):
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return bool(re.match(pattern, email))

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
            
        def _clear_tools():
            return "", "Enter a search term above and click 'Search Tools'"

        def _tool_search(query, num_results, backend_choice):
            if not query:
                yield "Please enter a search query.", "Enter a search term above and click 'Search Tools'"
                return
            status_msg = "Searching for AI tools related to your query... This may take a moment."
            yield status_msg, ""
            try:
                result = search_with_agent(query, backend_choice, num_results)
                # Robust tool block splitting: split on blank lines or 'Tool:'
                tool_blocks = re.split(r'\n(?=Tool: )|\n\s*\n', result)
                tools = []
                for block in tool_blocks:
                    lines = block.strip().split('\n')
                    current_tool = {}
                    for line in lines:
                        line = line.strip()
                        if line.startswith("Tool:"):
                            current_tool['name'] = line[5:].strip()
                        elif line.startswith("Description:"):
                            current_tool['description'] = line[12:].strip()
                        elif line.startswith("Pricing:"):
                            current_tool['pricing'] = line[8:].strip()
                    if 'name' in current_tool:
                        tools.append(current_tool)
                # Format as HTML
                if not tools:
                    yield "No structured tools parsed. Raw output:", f'<pre style="color:red">{result}</pre>'
                    return
                html = ""
                for tool in tools:
                    html += f'<div class="tool-result">'
                    html += f'<div class="tool-title">{tool.get("name", "Unknown Tool")}</div>'
                    if 'description' in tool:
                        html += f'<div class="tool-description">{tool.get("description", "")}</div>'
                    if 'pricing' in tool:
                        html += f'<div class="tool-tags"><b>Pricing:</b> {tool["pricing"]}</div>'
                    html += '</div>'
                yield "Search completed successfully.", html
            except Exception as e:
                yield "Search failed. Please try again with a different query.", ""

        def handle_subscribe(email):
            try:
                # Strict email validation
                if not is_valid_email(email):
                    return "Please enter a valid email address."
                
                # Add to database
                with Session() as session:
                    existing = session.query(Subscriber).filter_by(email=email).first()
                    if existing:
                        if existing.is_active:
                            return "You are already subscribed!"
                        else:
                            existing.is_active = True
                            session.commit()
                            return "Welcome back! Your subscription has been reactivated."
                    
                    new_subscriber = Subscriber(email=email)
                    session.add(new_subscriber)
                    session.commit()
                    return "Successfully subscribed to AI News Daily Summary!"
            except Exception as e:
                logger.error(f"Error in subscription: {str(e)}")
                return "Sorry, there was an error processing your subscription. Please try again."

        def handle_unsubscribe(email):
            try:
                # Validate email
                if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                    return "Please enter a valid email address."
                
                # Remove from database
                with Session() as session:
                    subscriber = session.query(Subscriber).filter_by(email=email).first()
                    if not subscriber or not subscriber.is_active:
                        return "This email is not subscribed."
                    
                    subscriber.is_active = False
                    session.commit()
                    return "Successfully unsubscribed from AI News Daily Summary."
            except Exception as e:
                logger.error(f"Error in unsubscription: {str(e)}")
                return "Sorry, there was an error processing your request. Please try again."

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

        tool_search_btn.click(
            _tool_search,
            inputs=[tool_query, num_results, backend],
            outputs=[tool_status, tool_results]
        )
        
        clear_tools_btn.click(
            _clear_tools,
            outputs=[tool_results, tool_status]
        )
        
        tool_query.submit(
            _tool_search,
            inputs=[tool_query, num_results, backend],
            outputs=[tool_status, tool_results]
        )

        subscribe_btn.click(
            handle_subscribe,
            inputs=[email_input],
            outputs=[subscription_status]
        )
        
        unsubscribe_btn.click(
            handle_unsubscribe,
            inputs=[email_input],
            outputs=[subscription_status]
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