from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse, HTMLResponse
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import logging
import threading
from queue import Queue
import time
from ultralytics import YOLO
import os
import torch
import asyncio
import base64
import winsound  # For Windows sound alerts
from datetime import datetime
from collections import defaultdict
from typing import List

def create_camera_app(model_name: str, camera_ip: str , alert_classes: List[str]):
    # Configure logging
    logging.basicConfig(level=logging.ERROR)
    logger = logging.getLogger(__name__)

    # Global variables
    frame_queue = Queue(maxsize=1)  # Single queue for one camera
    camera_thread = None
    is_running = False
    model = None
    device = None
    last_alert_time = defaultdict(float)  # Single alert time tracker
    ALERT_COOLDOWN = 5  # seconds between alerts

    # Alert classes and counters
    ALERT_CLASSES = alert_classes
    alert_counter = defaultdict(int)  # Single counter for alerts

    # Frame settings
    FRAME_WIDTH = 640  # Increased resolution for better detection
    FRAME_HEIGHT = 480
    FRAME_SKIP = 0  # Process every frame for better detection

    # Camera configuration
    CAMERA_URL = f"http://{camera_ip}/video"  # Single camera URL

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        nonlocal model, camera_thread, is_running, device
        
        try:
            # Check for CUDA availability
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            print(f"Using device: {device}")
            
            if not os.path.exists(model_name):
                raise FileNotFoundError(f"Model file not found at: {model_name}")
            
            # Load model and move to GPU
            model = YOLO(model_name)
            model.to(device)
            
            # Optimize for GPU
            model.fuse()
            model.conf = 0.3
            model.iou = 0.3
            
            # Start camera thread
            is_running = True
            camera_thread = threading.Thread(target=process_stream, daemon=True)
            camera_thread.start()
            yield
            
        except Exception as e:
            raise
        
        finally:
            is_running = False
            if camera_thread:
                camera_thread.join()

    app = FastAPI(title="Camera Streaming API", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def save_alert_screenshot(frame, alert_class, camera_id):
        """Save a screenshot when an alert is triggered"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"captures/camera{camera_id}_{alert_class}_{timestamp}.jpg"
        os.makedirs("captures", exist_ok=True)
        cv2.imwrite(filename, frame)
        logger.info(f"Saved alert screenshot: {filename}")

    def process_stream():
        cap = cv2.VideoCapture(CAMERA_URL, cv2.CAP_FFMPEG)
        
        if not cap.isOpened():
            logger.error("Failed to open camera stream")
            return
        
        # Set camera properties
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        while is_running and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            try:
                # Directly process frame with model
                results = model(frame, verbose=False, device=device, 
                              conf=0.4, iou=0.4, half=True)
                
                result = results[0]
                class_names = result.names
                
                # Initialize counters for current frame
                current_frame_counts = defaultdict(int)
                alert_triggered = False
                triggered_class = None
                
                # Process detections
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
                    cls = int(box.cls[0].cpu().numpy())
                    conf = box.conf[0].cpu().numpy()
                    class_name = class_names[cls]
                    
                    # Increment counter for this class
                    current_frame_counts[class_name] += 1
                    
                    # Check if this is an alert class
                    if class_name in ALERT_CLASSES and conf > 0.5:
                        alert_triggered = True
                        triggered_class = class_name
                        # Draw red rectangle for alert
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                        cv2.putText(frame, f"ALERT: {class_name} {conf:.1f}", (x1, y1 - 5),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    else:
                        # Draw normal green rectangle for other detections
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, f"{class_name} {conf:.1f}", (x1, y1 - 5),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                # Trigger alert if needed
                if alert_triggered and triggered_class:
                    current_time = time.time()
                    if (current_time - last_alert_time[triggered_class]) > ALERT_COOLDOWN:
                        last_alert_time[triggered_class] = current_time
                        alert_counter[triggered_class] += 1
                        
                        # Play alert sound
                        winsound.Beep(1000, 1000)
                        
                        # Save screenshot
                        save_alert_screenshot(frame, triggered_class, 0)
                        
                        # Log the alert
                        logger.warning(f"ALERT: {triggered_class} detected at {datetime.now()}")
                        
                        # Add visual alert overlay
                        counter_text = f"ALERT: {triggered_class.upper()} DETECTED!"
                        cv2.putText(frame, counter_text, (10, 30),
                                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
                # Display current frame detection counts
                y_offset = 70
                for alert_class in ALERT_CLASSES:
                    count = current_frame_counts[alert_class]
                    if count > 0:
                        counter_text = f"Current {alert_class}: {count}"
                        cv2.putText(frame, counter_text, (10, y_offset),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        y_offset += 30
                
                # Display total counts
                y_offset += 20
                cv2.putText(frame, "Total Counts:", (10, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                y_offset += 30
                
                for alert_class in ALERT_CLASSES:
                    total_count = alert_counter[alert_class]
                    counter_text = f"Total {alert_class}: {total_count}"
                    cv2.putText(frame, counter_text, (10, y_offset),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    y_offset += 30
                
                # Put processed frame in queue
                while not frame_queue.empty():
                    try:
                        frame_queue.get_nowait()
                    except:
                        pass
                    
                try:
                    frame_queue.put_nowait(frame)
                except:
                    pass
                
            except Exception as e:
                logger.error(f"Error processing frame: {str(e)}")
                continue
            
        cap.release()

    def generate_frames():
        while is_running:
            try:
                frame = frame_queue.get(timeout=0.1)
                if frame is not None:
                    # Encode frame
                    _, buffer = cv2.imencode('.jpg', frame, [
                        cv2.IMWRITE_JPEG_QUALITY, 80,
                        cv2.IMWRITE_JPEG_OPTIMIZE, 1
                    ])
                    
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            
            except:
                continue

    @app.get("/video_feed")
    async def video_feed():
        return StreamingResponse(
            generate_frames(),
            media_type='multipart/x-mixed-replace; boundary=frame'
        )

    @app.get("/", response_class=HTMLResponse)
    async def index():
        return """
        <html>
            <head>
                <title>Camera Stream</title>
                <style>
                    body {
                        margin: 0;
                        padding: 0;
                        width: 100vw;
                        height: 100vh;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        background-color: black;
                    }
                    img {
                        max-width: 100%;
                        max-height: 100vh;
                        object-fit: contain;
                    }
                </style>
            </head>
            <body>
                <img src="/video_feed" />
            </body>
        </html>
        """

    return app

if __name__ == "__main__":
    import uvicorn
    # Example usage
    app = create_camera_app("model.pt", "10.99.152.37:8080",[])
    uvicorn.run(app, host="0.0.0.0", port=8000) 