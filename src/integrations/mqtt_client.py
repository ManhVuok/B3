import json
import logging
import ssl
import threading
from datetime import datetime, timezone

from paho.mqtt import client as mqtt

from src.config import settings
from src.database import SessionLocal, generate_event_id
from src.schemas import AccessCheckRequest, RawRFIDEvent, ProcessedAccessEvent
from src.services.access_service import check_access

logger = logging.getLogger(__name__)

def on_connect(client, userdata, flags, reason_code, properties=None):
    logger.info("MQTT Connected with result code %s", reason_code)
    if reason_code == 0:
        client.subscribe(settings.mqtt_topic_input, qos=1)
        logger.info("Subscribed to topic: %s", settings.mqtt_topic_input)

def on_message(client, userdata, message):
    try:
        payload_str = message.payload.decode()
        logger.debug("Received MQTT message on %s: %s", message.topic, payload_str)
        data = json.loads(payload_str)
        
        # Parse incoming RawRFIDEvent
        raw_event = RawRFIDEvent(**data)
        
        # Build AccessCheckRequest for existing logic
        check_req = AccessCheckRequest(
            card_id=raw_event.uid,
            gate_id=raw_event.door_id,
            direction=raw_event.direction.upper(),
            timestamp=raw_event.timestamp
        )
        
        # Process logic via existing access_service
        with SessionLocal() as db:
            result = check_access(db, check_req)
            
        # Format the ProcessedAccessEvent
        now = datetime.now(timezone.utc)
        processed = ProcessedAccessEvent(
            event_id=result.event_id,
            timestamp=now,
            raw_event_id=raw_event.event_id,
            uid=raw_event.uid,
            student_id=result.person_id,
            full_name=result.person_name,
            # we don't have class_name in our model right now, we can skip or add logic later
            door_id=raw_event.door_id,
            location=raw_event.location,
            direction=raw_event.direction,
            access_result="granted" if result.access_granted else "denied",
            reason="uid_matched" if result.access_granted else ("uid_not_found" if "Unknown card" in result.reason else "denied")
        )
        
        # Publish back
        client.publish(
            settings.mqtt_topic_output, 
            processed.model_dump_json(), 
            qos=1
        )
        logger.info("Published MQTT processed event: %s", processed.event_id)
        
    except Exception as e:
        logger.error("Error processing MQTT message: %s", e)

def start_mqtt_client():
    def run():
        try:
            client = mqtt.Client(protocol=mqtt.MQTTv5)
            client.username_pw_set(settings.mqtt_username, settings.mqtt_password)
            client.tls_set(tls_version=ssl.PROTOCOL_TLS_CLIENT)

            client.on_connect = on_connect
            client.on_message = on_message

            client.connect(settings.mqtt_host, settings.mqtt_port, keepalive=60)
            client.loop_forever()
        except Exception as e:
            logger.error("Failed to start MQTT client: %s", e)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    logger.info("Background MQTT client thread started.")
