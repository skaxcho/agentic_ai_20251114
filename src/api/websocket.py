"""
WebSocket Support

Real-time updates for task and agent status
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict
import logging
import asyncio
import json

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        """Connect a new client"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Disconnect a client"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        # Remove from all subscriptions
        for topic, connections in self.subscriptions.items():
            if websocket in connections:
                connections.remove(websocket)

        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific client"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")

    async def broadcast(self, message: str):
        """Broadcast message to all connected clients"""
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to client: {str(e)}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    async def send_to_topic(self, topic: str, message: str):
        """Send message to subscribers of a specific topic"""
        if topic not in self.subscriptions:
            return

        disconnected = []

        for connection in self.subscriptions[topic]:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Failed to send to topic subscriber: {str(e)}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            if connection in self.subscriptions[topic]:
                self.subscriptions[topic].remove(connection)

    def subscribe(self, websocket: WebSocket, topic: str):
        """Subscribe client to a topic"""
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []

        if websocket not in self.subscriptions[topic]:
            self.subscriptions[topic].append(websocket)

        logger.info(f"Client subscribed to {topic}. Subscribers: {len(self.subscriptions[topic])}")

    def unsubscribe(self, websocket: WebSocket, topic: str):
        """Unsubscribe client from a topic"""
        if topic in self.subscriptions and websocket in self.subscriptions[topic]:
            self.subscriptions[topic].remove(websocket)
            logger.info(f"Client unsubscribed from {topic}")


# Global connection manager
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates

    Messages:
    - {"type": "subscribe", "topic": "tasks"} - Subscribe to topic
    - {"type": "unsubscribe", "topic": "tasks"} - Unsubscribe from topic
    - {"type": "ping"} - Keep-alive ping
    """
    await manager.connect(websocket)

    try:
        while True:
            # Receive message
            data = await websocket.receive_text()

            try:
                message = json.loads(data)

                if message.get("type") == "subscribe":
                    topic = message.get("topic")
                    if topic:
                        manager.subscribe(websocket, topic)
                        await manager.send_personal_message(
                            json.dumps({"type": "subscribed", "topic": topic}),
                            websocket
                        )

                elif message.get("type") == "unsubscribe":
                    topic = message.get("topic")
                    if topic:
                        manager.unsubscribe(websocket, topic)
                        await manager.send_personal_message(
                            json.dumps({"type": "unsubscribed", "topic": topic}),
                            websocket
                        )

                elif message.get("type") == "ping":
                    await manager.send_personal_message(
                        json.dumps({"type": "pong"}),
                        websocket
                    )

            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({"type": "error", "message": "Invalid JSON"}),
                    websocket
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket)


async def broadcast_task_update(task_id: str, status: str, data: Dict):
    """Broadcast task status update"""
    message = json.dumps({
        "type": "task_update",
        "task_id": task_id,
        "status": status,
        "data": data,
        "timestamp": asyncio.get_event_loop().time()
    })

    await manager.send_to_topic("tasks", message)


async def broadcast_agent_update(agent_type: str, data: Dict):
    """Broadcast agent status update"""
    message = json.dumps({
        "type": "agent_update",
        "agent_type": agent_type,
        "data": data,
        "timestamp": asyncio.get_event_loop().time()
    })

    await manager.send_to_topic(f"agent:{agent_type}", message)
    await manager.send_to_topic("agents", message)
