from aggregator.subscription_ui import launch_subscription_ui
from aggregator.scheduler import setup_weekly_digest_scheduler
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    # Start the scheduler for weekly digests
    setup_weekly_digest_scheduler()
    
    # Launch the subscription UI
    demo = launch_subscription_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7861,  # Different port from main UI
        share=True
    ) 