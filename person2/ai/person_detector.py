"""Run YOLOv8n person detection on a video and save an annotated MP4."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import cv2
from ultralytics import YOLO

from sensor_intelligence import DEFAULT_THRESHOLDS, SensorSimulator, evaluate_hazards


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Detect people (COCO class 0) in a video using YOLOv8n."
    )
    parser.add_argument(
        "--source", type=Path,
        default=Path("person2/videos/mine_worker_sample.mp4"),
        help="Input video path (default: the bundled mine sample).",
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("person2/results/person_detection_output.mp4"),
        help="Where to save the annotated video.",
    )
    parser.add_argument("--model", default="yolov8n.pt", help="YOLO weights (default: yolov8n.pt).")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold, 0 to 1.")
    parser.add_argument("--imgsz", type=int, default=640, help="YOLO inference image size.")
    parser.add_argument(
        "--events-output",
        type=Path,
        help="JSON event report path (default: the output video path with a .json extension).",
    )
    parser.add_argument(
        "--sensor-interval",
        type=float,
        default=1.0,
        help="Seconds between simulated sensor readings.",
    )
    parser.add_argument("--sensor-seed", type=int, default=42, help="Seed for repeatable sensor simulation.")
    parser.add_argument(
        "--sensor-scenario",
        choices=("normal", "hazard-demo"),
        default="normal",
        help="Use safe-range readings, or inject a clearly simulated hazard at the third sample.",
    )
    args = parser.parse_args()
    if not 0.0 <= args.conf <= 1.0:
        parser.error("--conf must be between 0 and 1")
    if args.imgsz < 32:
        parser.error("--imgsz must be at least 32")
    if args.sensor_interval <= 0:
        parser.error("--sensor-interval must be greater than 0")
    if args.events_output is None:
        args.events_output = args.output.with_suffix(".json")
    return args


def make_event(
    event_number: int,
    event_type: str,
    timestamp_seconds: float,
    source: str,
    severity: str,
    data: dict,
    message: str,
) -> dict:
    return {
        "event_id": f"event-{event_number:06d}",
        "event_type": event_type,
        "timestamp_seconds": round(timestamp_seconds, 3),
        "source": source,
        "severity": severity,
        "message": message,
        "data": data,
    }


def main() -> int:
    args = parse_args()
    if not args.source.is_file():
        print(f"ERROR: Input video not found: {args.source.resolve()}", file=sys.stderr)
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    print(f"Loading model: {args.model}")
    print("On the first run, Ultralytics may download the YOLO weights (internet required).")
    model = YOLO(args.model)

    cap = cv2.VideoCapture(str(args.source))
    if not cap.isOpened():
        print(f"ERROR: Could not open video: {args.source.resolve()}", file=sys.stderr)
        return 3

    fps = cap.get(cv2.CAP_PROP_FPS)
    fps = fps if fps and fps > 0 else 15.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    writer = cv2.VideoWriter(
        str(args.output), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
    )
    if not writer.isOpened():
        cap.release()
        print(f"ERROR: Could not create output video: {args.output.resolve()}", file=sys.stderr)
        return 4

    frame_count = 0
    frames_with_people = 0
    total_person_detections = 0
    best_confidence = 0.0
    sensor_simulator = SensorSimulator(args.sensor_seed, args.sensor_scenario)
    sensor_readings = []
    events = []
    next_sensor_time = 0.0

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            timestamp_seconds = frame_count / fps
            result = model.predict(
                source=frame,
                classes=[0],  # COCO class 0 = person
                conf=args.conf,
                imgsz=args.imgsz,
                verbose=False,
            )[0]

            boxes = result.boxes
            count = 0 if boxes is None else len(boxes)
            frame_count += 1
            total_person_detections += count
            if count:
                frames_with_people += 1
                confidences = boxes.conf.tolist()
                best_confidence = max(best_confidence, max(confidences))
                detections = [
                    {
                        "class": "person",
                        "confidence": round(float(confidence), 4),
                        "bbox_xyxy": [round(float(value), 2) for value in box],
                    }
                    for box, confidence in zip(boxes.xyxy.tolist(), confidences)
                ]
                events.append(
                    make_event(
                        len(events) + 1,
                        "survivor_detected",
                        timestamp_seconds,
                        "camera",
                        "info",
                        {
                            "subject_type": "potential_survivor",
                            "status": "visual person detection; survival and condition unverified",
                            "detections": detections,
                        },
                        "A person was detected in the video; this does not confirm survivor status.",
                    )
                )

            annotated = result.plot()
            writer.write(annotated)

            if timestamp_seconds + 1e-9 >= next_sensor_time:
                reading = sensor_simulator.sample(timestamp_seconds)
                sensor_readings.append(reading)
                for hazard in evaluate_hazards(reading):
                    events.append(
                        make_event(
                            len(events) + 1,
                            "hazard_detected",
                            timestamp_seconds,
                            "simulated_sensor",
                            str(hazard["severity"]),
                            hazard,
                            (
                                f"Simulated {hazard['sensor']} reading crossed its "
                                f"{hazard['severity']} threshold."
                            ),
                        )
                    )
                next_sensor_time += args.sensor_interval

    finally:
        cap.release()
        writer.release()

    report = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "simulation_only": True,
        "safety_notice": (
            "Sensor readings are simulated, and person detections do not verify survival. "
            "This output is for demonstration only, not for operational mine-safety decisions."
        ),
        "source_video": args.source.name,
        "annotated_video": args.output.name,
        "sensor_scenario": args.sensor_scenario,
        "summary": {
            "frames_processed": frame_count,
            "frames_with_person_detections": frames_with_people,
            "person_detections": total_person_detections,
            "sensor_samples": len(sensor_readings),
            "survivor_events": sum(event["event_type"] == "survivor_detected" for event in events),
            "hazard_events": sum(event["event_type"] == "hazard_detected" for event in events),
            "highest_person_confidence": round(best_confidence, 4),
        },
        "sensor_thresholds": {
            name: {
                "warning": threshold.warning,
                "critical": threshold.critical,
                "unit": threshold.unit,
            }
            for name, threshold in DEFAULT_THRESHOLDS.items()
        },
        "sensor_readings": sensor_readings,
        "events": events,
    }
    args.events_output.parent.mkdir(parents=True, exist_ok=True)
    with args.events_output.open("w", encoding="utf-8") as event_file:
        json.dump(report, event_file, indent=2)
        event_file.write("\n")

    print("\n--- Detection summary ---")
    print(f"Frames processed: {frame_count}")
    print(f"Frames containing a person detection: {frames_with_people}")
    print(f"Total person detections across frames: {total_person_detections}")
    print(f"Highest confidence: {best_confidence:.3f}")
    print(f"Annotated video saved to: {args.output.resolve()}")
    print(f"JSON event report saved to: {args.events_output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
