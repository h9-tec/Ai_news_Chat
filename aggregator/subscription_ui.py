import gradio as gr
from models import Subscription
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import re
import logging

logger = logging.getLogger(__name__)

# Create database engine and session
engine = create_engine('sqlite:///news.db')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def launch_subscription_ui():
    with gr.Blocks(css="""
        .subscription-container {
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #1a1a1a;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            color: #ffffff;
        }
        .form-container {
            background-color: #2d2d2d;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .status-message {
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
        }
        .success {
            background-color: #1e4620;
            color: #4caf50;
        }
        .error {
            background-color: #461e1e;
            color: #f44336;
        }
    """) as demo:
        with gr.Column(elem_classes="subscription-container"):
            gr.Markdown("# 📬 AI News Weekly Digest", elem_classes="header")
            gr.Markdown("""
            Subscribe to receive weekly summaries of the latest AI news and developments.
            - Comprehensive weekly roundup of AI news
            - Curated content from top AI news sources
            - Delivered every Sunday
            - Easy unsubscribe at any time
            """)
            
            with gr.Column(elem_classes="form-container"):
                email_input = gr.Textbox(
                    placeholder="your.email@example.com",
                    label="Email Address",
                    scale=1
                )
                with gr.Row():
                    subscribe_btn = gr.Button("Subscribe", variant="primary", scale=2)
                    unsubscribe_btn = gr.Button("Unsubscribe", scale=1)
                
                status = gr.Markdown(elem_classes="status-message")

        def handle_subscribe(email):
            try:
                # Strict email validation
                if not is_valid_email(email):
                    return "⚠️ Please enter a valid email address."
                
                # Add to database
                db = SessionLocal()
                try:
                    existing = db.query(Subscription).filter_by(email=email).first()
                    if existing:
                        if existing.is_active:
                            return "ℹ️ You are already subscribed!"
                        else:
                            existing.is_active = True
                            db.commit()
                            return "✅ Welcome back! Your subscription has been reactivated."
                    
                    new_subscription = Subscription(email=email)
                    db.add(new_subscription)
                    db.commit()
                    return "✅ Successfully subscribed to AI News Weekly Digest!"
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"Error in subscription: {str(e)}")
                return "❌ Sorry, there was an error processing your subscription. Please try again."

        def handle_unsubscribe(email):
            try:
                # Validate email
                if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                    return "⚠️ Please enter a valid email address."
                
                # Remove from database
                db = SessionLocal()
                try:
                    subscription = db.query(Subscription).filter_by(email=email).first()
                    if not subscription or not subscription.is_active:
                        return "ℹ️ This email is not subscribed."
                    
                    subscription.is_active = False
                    db.commit()
                    return "✅ Successfully unsubscribed from AI News Weekly Digest."
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"Error in unsubscription: {str(e)}")
                return "❌ Sorry, there was an error processing your request. Please try again."

        # Wire up the subscription buttons
        subscribe_btn.click(
            handle_subscribe,
            inputs=[email_input],
            outputs=[status]
        )
        
        unsubscribe_btn.click(
            handle_unsubscribe,
            inputs=[email_input],
            outputs=[status]
        )

    return demo

if __name__ == "__main__":
    demo = launch_subscription_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7861,  # Different port from main UI
        share=True
    ) 