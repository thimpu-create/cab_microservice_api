# Testing Realtime Service - Complete Guide

## 🎯 Overview

The realtime service handles:
1. **WebSocket connections** for drivers and passengers
2. **Ride requests** via HTTP endpoint
3. **Real-time location updates** between drivers and passengers
4. **Ride matching** using Redis GEO queries

---

## 📍 Service Endpoints

**Base URL:** `http://localhost:8007` (realtime-service)  
**WebSocket URL:** `ws://localhost:8007`

---

## 🚗 Complete Testing Flow

### **Step 1: Connect Driver via WebSocket**

**WebSocket Endpoint:**
```
ws://localhost:8007/ws/driver/{driver_id}
```

**Example:**
```
ws://localhost:8007/ws/driver/driver-123
```

**What happens:**
- Driver is added to `available_drivers` set in Redis
- Driver location can now be updated
- Driver will receive ride requests

---

### **Step 2: Driver Sends Location Updates**

**Message Format (JSON):**
```json
{
  "lat": 40.7128,
  "lon": -74.0060,
  "status": "available"
}
```

**Send periodically (every 5-10 seconds)** to update driver's position.

---

### **Step 3: Passenger Requests a Ride**

**HTTP Endpoint:**
```
POST http://localhost:8007/api/v1/ride/request
```

**Request Body:**
```json
{
  "passenger_id": "passenger-456",
  "lat": 40.7580,
  "lon": -73.9855
}
```

**Response:**
```json
{
  "status": "request_sent",
  "request_id": "abc-123-def-456"
}
```

**What happens:**
- System finds nearby drivers (within 10km)
- Sends ride request to all available drivers via WebSocket
- Drivers receive: `{"type": "ride_request", "request_id": "...", "passenger_id": "...", "pickup_lat": ..., "pickup_lon": ...}`

---

### **Step 4: Driver Accepts Ride**

**Driver sends via WebSocket:**
```json
{
  "type": "accept_ride",
  "request_id": "abc-123-def-456"
}
```

**Driver receives confirmation:**
```json
{
  "type": "ride_confirmed",
  "passenger_id": "passenger-456",
  "pickup_lat": 40.7580,
  "pickup_lon": -73.9855,
  "request_id": "abc-123-def-456"
}
```

**Passenger receives notification:**
```json
{
  "type": "driver_assigned",
  "driver_id": "driver-123",
  "pickup_lat": 40.7580,
  "pickup_lon": -73.9855
}
```

---

### **Step 5: Connect Passenger via WebSocket**

**WebSocket Endpoint:**
```
ws://localhost:8007/ws/passenger/{passenger_id}
```

**Example:**
```
ws://localhost:8007/ws/passenger/passenger-456
```

---

### **Step 6: Driver Sends Location Updates (During Ride)**

While in a ride, driver's location updates are automatically sent to the passenger:

**Driver sends:**
```json
{
  "lat": 40.7600,
  "lon": -73.9840,
  "status": "on_ride"
}
```

**Passenger automatically receives:**
```json
{
  "type": "driver_location_update",
  "driver_id": "driver-123",
  "lat": 40.7600,
  "lon": -73.9840
}
```

---

### **Step 7: Driver Completes Ride**

**Driver sends via WebSocket:**
```json
{
  "type": "completed_ride",
  "request_id": "abc-123-def-456"
}
```

**Driver receives:**
```json
{
  "type": "ride_completed_ack",
  "request_id": "abc-123-def-456"
}
```

**Passenger receives:**
```json
{
  "type": "ride_completed",
  "request_id": "abc-123-def-456"
}
```

---

## 🧪 Testing Tools

### **Option 1: Browser Console (JavaScript)**

#### **Driver Connection:**
```javascript
const driverId = 'driver-123';
const driverWs = new WebSocket(`ws://localhost:8007/ws/driver/${driverId}`);

driverWs.onopen = () => {
  console.log('Driver connected');
  
  // Send location update
  driverWs.send(JSON.stringify({
    lat: 40.7128,
    lon: -74.0060,
    status: 'available'
  }));
};

driverWs.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Driver received:', data);
  
  // If ride request received, accept it
  if (data.type === 'ride_request') {
    driverWs.send(JSON.stringify({
      type: 'accept_ride',
      request_id: data.request_id
    }));
  }
};

driverWs.onerror = (error) => {
  console.error('Driver WebSocket error:', error);
};

driverWs.onclose = () => {
  console.log('Driver disconnected');
};
```

#### **Passenger Connection:**
```javascript
const passengerId = 'passenger-456';
const passengerWs = new WebSocket(`ws://localhost:8007/ws/passenger/${passengerId}`);

passengerWs.onopen = () => {
  console.log('Passenger connected');
};

passengerWs.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Passenger received:', data);
};

passengerWs.onerror = (error) => {
  console.error('Passenger WebSocket error:', error);
};

passengerWs.onclose = () => {
  console.log('Passenger disconnected');
};

// Request a ride
async function requestRide() {
  const response = await fetch('http://localhost:8007/api/v1/ride/request', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      passenger_id: passengerId,
      lat: 40.7580,
      lon: -73.9855
    })
  });
  
  const result = await response.json();
  console.log('Ride requested:', result);
}

requestRide();
```

---

### **Option 2: Python Script**

```python
import asyncio
import websockets
import json
import httpx

# Driver WebSocket
async def driver_connection():
    driver_id = "driver-123"
    uri = f"ws://localhost:8007/ws/driver/{driver_id}"
    
    async with websockets.connect(uri) as websocket:
        print(f"🚗 Driver {driver_id} connected")
        
        # Send location update
        await websocket.send(json.dumps({
            "lat": 40.7128,
            "lon": -74.0060,
            "status": "available"
        }))
        
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Driver received: {data}")
            
            # Auto-accept ride requests
            if data.get("type") == "ride_request":
                await websocket.send(json.dumps({
                    "type": "accept_ride",
                    "request_id": data["request_id"]
                }))
                print(f"✅ Accepted ride {data['request_id']}")
            
            # Send periodic location updates
            await asyncio.sleep(5)
            await websocket.send(json.dumps({
                "lat": 40.7128,
                "lon": -74.0060,
                "status": "available"
            }))

# Passenger WebSocket
async def passenger_connection():
    passenger_id = "passenger-456"
    uri = f"ws://localhost:8007/ws/passenger/{passenger_id}"
    
    async with websockets.connect(uri) as websocket:
        print(f"👤 Passenger {passenger_id} connected")
        
        # Request a ride
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8007/api/v1/ride/request",
                json={
                    "passenger_id": passenger_id,
                    "lat": 40.7580,
                    "lon": -73.9855
                }
            )
            print(f"Ride requested: {response.json()}")
        
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Passenger received: {data}")

# Run both
async def main():
    await asyncio.gather(
        driver_connection(),
        passenger_connection()
    )

if __name__ == "__main__":
    asyncio.run(main())
```

---

### **Option 3: Postman / Thunder Client**

**For Ride Request (HTTP):**
- Method: `POST`
- URL: `http://localhost:8007/api/v1/ride/request`
- Body (JSON):
```json
{
  "passenger_id": "passenger-456",
  "lat": 40.7580,
  "lon": -73.9855
}
```

**For WebSocket:** Use a WebSocket client extension/tool.

---

### **Option 4: wscat (Command Line)**

Install: `npm install -g wscat`

**Driver:**
```bash
wscat -c ws://localhost:8007/ws/driver/driver-123
```

**Send messages:**
```json
{"lat": 40.7128, "lon": -74.0060, "status": "available"}
{"type": "accept_ride", "request_id": "abc-123"}
```

**Passenger:**
```bash
wscat -c ws://localhost:8007/ws/passenger/passenger-456
```

---

## 📊 Complete Test Scenario

### **Terminal 1: Start Driver**
```bash
# Using Python
python -c "
import asyncio, websockets, json
async def test():
    async with websockets.connect('ws://localhost:8007/ws/driver/driver-1') as ws:
        await ws.send(json.dumps({'lat': 40.7128, 'lon': -74.0060, 'status': 'available'}))
        async for msg in ws:
            print('Driver:', json.loads(msg))
asyncio.run(test())
"
```

### **Terminal 2: Request Ride (HTTP)**
```bash
curl -X POST http://localhost:8007/api/v1/ride/request \
  -H "Content-Type: application/json" \
  -d '{
    "passenger_id": "passenger-1",
    "lat": 40.7580,
    "lon": -73.9855
  }'
```

### **Terminal 3: Connect Passenger**
```bash
python -c "
import asyncio, websockets, json
async def test():
    async with websockets.connect('ws://localhost:8007/ws/passenger/passenger-1') as ws:
        async for msg in ws:
            print('Passenger:', json.loads(msg))
asyncio.run(test())
"
```

---

## 📋 Message Types Reference

### **Driver → Server:**
| Type | Description | Payload |
|------|-------------|---------|
| Location Update | Update driver position | `{"lat": float, "lon": float, "status": string}` |
| Accept Ride | Accept a ride request | `{"type": "accept_ride", "request_id": string}` |
| Complete Ride | Mark ride as completed | `{"type": "completed_ride", "request_id": string}` |

### **Server → Driver:**
| Type | Description | Payload |
|------|-------------|---------|
| Ride Request | New ride request | `{"type": "ride_request", "request_id": string, "passenger_id": string, "pickup_lat": float, "pickup_lon": float}` |
| Ride Confirmed | Ride acceptance confirmed | `{"type": "ride_confirmed", "passenger_id": string, "pickup_lat": float, "pickup_lon": float, "request_id": string}` |
| Ride Taken | Ride already taken by another driver | `{"type": "ride_taken", "request_id": string}` |
| Ongoing Ride | Ride state restored on reconnect | `{"type": "ongoing_ride", "passenger_id": string, "pickup_lat": float, "pickup_lon": float, "request_id": string, "status": string}` |
| Ride Completed ACK | Ride completion confirmed | `{"type": "ride_completed_ack", "request_id": string}` |

### **Server → Passenger:**
| Type | Description | Payload |
|------|-------------|---------|
| Driver Assigned | Driver accepted ride | `{"type": "driver_assigned", "driver_id": string, "pickup_lat": float, "pickup_lon": float}` |
| Driver Location Update | Driver's current location | `{"type": "driver_location_update", "driver_id": string, "lat": float, "lon": float}` |
| Ongoing Ride | Ride state restored on reconnect | `{"type": "ongoing_ride", "driver_id": string, "pickup_lat": float, "pickup_lon": float, "status": string}` |
| Ride Completed | Ride finished | `{"type": "ride_completed", "request_id": string}` |

---

## ✅ Test Checklist

- [ ] Driver connects via WebSocket
- [ ] Driver sends location updates
- [ ] Driver appears in Redis GEO index
- [ ] Passenger requests ride (HTTP)
- [ ] Driver receives ride request via WebSocket
- [ ] Driver accepts ride
- [ ] Passenger receives driver assignment
- [ ] Driver location updates sent to passenger during ride
- [ ] Driver completes ride
- [ ] Passenger receives completion notification
- [ ] Driver returns to available status

---

## 🐛 Troubleshooting

### **Driver not receiving requests?**
- Check if driver sent location update first
- Verify driver is within 10km of pickup location
- Check Redis: `redis-cli SMEMBERS available_drivers`

### **WebSocket connection fails?**
- Verify service is running: `curl http://localhost:8007/health`
- Check Redis is running
- Verify WebSocket URL format: `ws://localhost:8007/ws/driver/{id}`

### **No drivers found?**
- Ensure at least one driver has sent location update
- Check Redis GEO: `redis-cli GEORADIUS drivers_geo -74.0060 40.7128 10 km`

---

## 📚 Quick Reference

**Service Port:** `8007`  
**Health Check:** `GET http://localhost:8007/health`  
**Request Ride:** `POST http://localhost:8007/api/v1/ride/request`  
**Driver WS:** `ws://localhost:8007/ws/driver/{driver_id}`  
**Passenger WS:** `ws://localhost:8007/ws/passenger/{passenger_id}`
