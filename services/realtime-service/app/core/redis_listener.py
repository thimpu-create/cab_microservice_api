from app.core.redis_client import redis_conn


def listen_to_redis():
    """Listen to Redis pub/sub for ride events."""
    pub = redis_conn.pubsub()
    pub.subscribe("ride_channel")
    print("✅ Subscribed to Redis ride_channel...")
    
    for msg in pub.listen():
        if msg["type"] == "message":
            try:
                data = msg["data"]
                if isinstance(data, bytes):
                    data = data.decode()
                print("📨 Redis message →", data)
                # Process message if needed
            except Exception as e:
                print(f"❌ Error processing Redis message: {e}")
