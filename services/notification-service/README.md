# Notification Service

FastAPI-based notification service with Firebase Cloud Messaging (FCM) integration for sending push notifications, SMS, email, and in-app notifications.

## Features

- ✅ **Firebase Cloud Messaging (FCM)** - Native push notifications for iOS and Android
- ✅ **Topic-based Messaging** - Send notifications to groups of users
- ✅ **Multicast Messaging** - Send to multiple devices at once
- ✅ **Multi-channel Support** - Push, SMS, Email, In-app
- ✅ **Priority Levels** - High, normal priority for notifications
- ✅ **Bulk Operations** - Send to thousands of users simultaneously
- ✅ **Ride Lifecycle Notifications** - Ride request, driver assigned, status updates
- ✅ **Structured Logging** - Comprehensive logging for debugging

## Architecture

```
notification-service/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── notifications.py      # All notification endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                 # Configuration management
│   │   ├── events.py                 # App lifecycle events
│   │   ├── firebase.py               # Firebase service logic
│   │   └── security.py               # Security utilities
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── notification.py           # Pydantic models
│   ├── db/                           # Database models (if needed)
│   ├── __init__.py
│   └── main.py                       # FastAPI app initialization
├── firebase-key.json                 # Firebase service account credentials
├── .env                              # Environment variables
├── .env.example                      # Environment template
├── requirements.txt                  # Python dependencies
├── Dockerfile                        # Docker configuration
└── README.md                         # This file
```

## Firebase Setup

### 1. Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or use existing one
3. Enable Firebase Cloud Messaging (FCM)

### 2. Get Service Account Credentials

1. In Firebase Console, go to **Project Settings** > **Service Accounts**
2. Click **Generate New Private Key**
3. Save the JSON file as `firebase-key.json` in the notification-service root directory

### 3. Environment Variables

Create a `.env` file:

```bash
FIREBASE_KEY_PATH=firebase-key.json
FIREBASE_PROJECT_ID=your-project-id
DEBUG=False
```

Or copy from `.env.example`:

```bash
cp .env.example .env
```

## Installation

### Local Development

1. **Install dependencies:**

```bash
pip install -r requirements.txt
```

2. **Place Firebase key:**

```bash
# Copy your firebase-key.json to the service root
cp path/to/firebase-key.json ./firebase-key.json
```

3. **Run the service:**

```bash
python -m uvicorn app.main:app --reload --port 8006
```

Visit: http://localhost:8006/docs

### Docker

Build and run:

```bash
docker build -t notification-service .
docker run -p 8006:8006 \
  -v $(pwd)/firebase-key.json:/app/firebase-key.json \
  -e FIREBASE_KEY_PATH=/app/firebase-key.json \
  notification-service
```

## API Endpoints

### 1. Send Single Notification

**POST** `/api/v1/notifications/send`

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "notification_type": "ride_request",
  "title": "New Ride Request",
  "message": "A new ride request is available",
  "channels": ["in_app", "push"],
  "data": {
    "request_id": "req-123",
    "distance_km": 5.2
  },
  "priority": "high"
}
```

### 2. Send Bulk Notifications

**POST** `/api/v1/notifications/send/bulk`

```json
{
  "user_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "550e8400-e29b-41d4-a716-446655440001"
  ],
  "notification_type": "ride_request",
  "title": "New Ride Request",
  "message": "A new ride request is available",
  "channels": ["push"],
  "priority": "high"
}
```

### 3. Send Direct Push Notification (Firebase)

**POST** `/api/v1/notifications/push`

```json
{
  "device_token": "eT9NacZ4QwSZJgL...",
  "title": "Driver Arrived",
  "body": "Your driver has arrived",
  "data": {
    "request_id": "req-123",
    "driver_id": "drv-456"
  },
  "priority": "high"
}
```

### 4. Send Multicast Push Notifications

**POST** `/api/v1/notifications/push/multicast`

```json
{
  "device_tokens": [
    "eT9NacZ4QwSZJgL...",
    "fU0PbdZ5RxTaKhM..."
  ],
  "title": "New Ride Available",
  "body": "5.2 km away",
  "priority": "high"
}
```

### 5. Send to Topic

**POST** `/api/v1/notifications/topic/send`

```json
{
  "topic": "drivers",
  "title": "System Maintenance",
  "body": "Service will be down for 30 minutes",
  "priority": "normal"
}
```

### 6. Subscribe Devices to Topic

**POST** `/api/v1/notifications/topic/subscribe`

```json
{
  "device_tokens": ["eT9NacZ4QwSZJgL..."],
  "topic": "drivers"
}
```

### 7. Unsubscribe Devices from Topic

**POST** `/api/v1/notifications/topic/unsubscribe`

```json
{
  "device_tokens": ["eT9NacZ4QwSZJgL..."],
  "topic": "drivers"
}
```

### 8. Ride Request Notification

**POST** `/api/v1/notifications/ride/request-sent`

```json
{
  "driver_ids": ["550e8400-e29b-41d4-a716-446655440000"],
  "passenger_id": "550e8400-e29b-41d4-a716-446655440100",
  "request_id": "req-123",
  "pickup_lat": 40.7128,
  "pickup_lon": -74.0060,
  "distance_km": 5.2,
  "pickup_address": "123 Main St, New York",
  "device_tokens": ["eT9NacZ4QwSZJgL..."]
}
```

### 9. Driver Assigned Notification

**POST** `/api/v1/notifications/ride/driver-assigned`

```json
{
  "passenger_id": "550e8400-e29b-41d4-a716-446655440100",
  "driver_id": "550e8400-e29b-41d4-a716-446655440000",
  "request_id": "req-123",
  "pickup_lat": 40.7128,
  "pickup_lon": -74.0060,
  "device_token": "eT9NacZ4QwSZJgL..."
}
```

### 10. Ride Status Update

**POST** `/api/v1/notifications/ride/status-update`

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440100",
  "notification_type": "ride_started",
  "request_id": "req-123",
  "title": "Ride Started",
  "message": "Your ride has started",
  "device_token": "eT9NacZ4QwSZJgL..."
}
```

## Firebase Topics

Standard topics for your ride-sharing app:

```
drivers          - All drivers
passengers       - All passengers
admins           - Administrators
support          - Support team
emergency        - Emergency alerts
rides-active     - Users with active rides
promo            - Promotional messages
system-alerts    - System-wide alerts
```

## FirebaseService Class

The `FirebaseService` provides these methods:

```python
# Send to single device
FirebaseService.send_push_notification(
    device_token="...",
    title="Title",
    body="Message",
    data={...},
    priority="high"
)

# Send to multiple devices
FirebaseService.send_multicast_notification(
    device_tokens=["...", "..."],
    title="Title",
    body="Message",
    data={...},
    priority="high"
)

# Subscribe to topic
FirebaseService.subscribe_to_topic(
    device_tokens=["..."],
    topic="drivers"
)

# Unsubscribe from topic
FirebaseService.unsubscribe_from_topic(
    device_tokens=["..."],
    topic="drivers"
)

# Send to topic subscribers
FirebaseService.send_to_topic(
    topic="drivers",
    title="Title",
    body="Message",
    data={...},
    priority="high"
)
```

## Integration with Other Services

### From Ride Service

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://notification-service:8006/api/v1/notifications/ride/request-sent",
        json={
            "driver_ids": driver_ids,
            "passenger_id": passenger_id,
            "request_id": request_id,
            "pickup_lat": 40.7128,
            "pickup_lon": -74.0060,
            "distance_km": 5.2,
            "device_tokens": device_tokens
        }
    )
```

## Error Handling

Common error responses:

```json
{
  "detail": "Invalid device token"
}

{
  "detail": "Failed to send push notification"
}

{
  "detail": "Invalid user ID format"
}

{
  "detail": "Maximum bulk size is 1000 users"
}
```

## Logging

The service logs all operations:

```
2024-01-28 10:30:45 - app.core.firebase - INFO - ✅ Firebase Admin SDK initialized successfully
2024-01-28 10:30:46 - app.api.v1.notifications - INFO - 📧 Notification for user 550e8400-e29b-41d4-a716-446655440000: ride_request
2024-01-28 10:30:47 - app.core.firebase - INFO - ✅ Push notification sent: abc123def456
```

## Database Integration (Future)

To store notification history:

```python
# models.py
class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey("users.id"))
    type = Column(String)
    title = Column(String)
    message = Column(String)
    channels_sent = Column(JSON)
    status = Column(String)  # sent, failed, pending
    created_at = Column(DateTime, default=datetime.utcnow)
```

## Performance Considerations

- Multicast sends up to 500 devices per request
- For larger batches, split into chunks of 500
- Use topic messaging for broadcasting to thousands
- Device token subscription is fast and can be batched

## Security

- Firebase credentials are stored securely in `firebase-key.json`
- Never commit `firebase-key.json` to version control
- Use environment variables for sensitive data
- Validate all input UUIDs
- Implement rate limiting on endpoints

## Testing

Local testing with device tokens:

```bash
# Get a test device token from your mobile app
# Send test notification via API
curl -X POST http://localhost:8006/api/v1/notifications/push \
  -H "Content-Type: application/json" \
  -d '{
    "device_token": "YOUR_TEST_TOKEN",
    "title": "Test",
    "body": "Test notification",
    "priority": "high"
  }'
```

## Troubleshooting

### Firebase Not Initialized
- Verify `firebase-key.json` exists in correct location
- Check `FIREBASE_KEY_PATH` environment variable
- Review logs for initialization errors

### Push Notifications Not Received
- Verify device token is valid and fresh
- Check device token hasn't been revoked
- Ensure FCM is enabled in Firebase Console
- Verify app is properly registered with FCM

### Multicast Sending Issues
- Limit device tokens to 500 per request
- Validate all tokens before sending
- Check Firebase quota limits

## References

- [Firebase Admin SDK Python](https://firebase.google.com/docs/admin/setup)
- [Firebase Cloud Messaging](https://firebase.google.com/docs/cloud-messaging)
- [FCM Message Structure](https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
