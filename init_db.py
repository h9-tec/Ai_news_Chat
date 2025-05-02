from aggregator.database import init_db
from aggregator.models import Subscriber  # Import to register the model

if __name__ == "__main__":
    print("Creating database tables...")
    init_db()
    print("Database tables created successfully!") 