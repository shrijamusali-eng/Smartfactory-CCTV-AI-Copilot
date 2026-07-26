import logging
from cctv.safety_engine import check, get_model
from cctv.tracker import track
from cctv.violation_tracker import ViolationTracker
from cctv.incident_pipeline import handle_violations
from cctv.stream import get_frames

logger = logging.getLogger(__name__)

# Configurable frame processing throttle limit per camera pass sweep
MAX_FRAMES_PER_CAMERA = 30

def run_all_cameras(progress_callback=None, run_id=None):
    """
    Simulates or processes all registered factory cameras, running safety inference 
    and routing tracked violations cleanly with the active session's run_id identity.
    """
    # Active factory camera stream registry mapping matrix
    registered_cameras = [
        {"name": "Main Entrance", "zone": "Zone A", "source": "main_entrance.mp4"},
        {"name": "Assembly Line 1", "zone": "Assembly Area", "source": "assembly_1.mp4"},
        {"name": "Loading Dock", "zone": "Warehouse", "source": "loading_dock.mp4"}
    ]
    
    yolo_model = get_model()
    
    for camera in registered_cameras:
        camera_name = camera["name"]
        zone_name = camera["zone"]
        source_path = camera["source"]
        
        # FIX: Instantiate a completely independent tracker state per camera feed 
        # to ensure no object trajectory leakage occurs between physical zones.
        tracker = ViolationTracker(timeout_seconds=3)
        
        try:
            frames = get_frames(source_path)
            
            for i, frame in enumerate(frames):
                if i >= MAX_FRAMES_PER_CAMERA:
                    break
                    
                results = yolo_model.predict(source=frame, conf=0.35, verbose=False)
                tracked = track(results[0])
                violations = check(tracked, yolo_model.names)
                
                handle_violations(
                    violations=violations,
                    frame=frame,
                    tracker_instance=tracker,
                    camera=camera_name,
                    zone=zone_name,
                    is_last_frame=False,
                    run_id=run_id
                )
                
            # Safely flush this specific camera's tracking queues at the stream boundary
            handle_violations(
                violations=[],
                frame=None,
                tracker_instance=tracker,
                camera=camera_name,
                zone=zone_name,
                is_last_frame=True,
                run_id=run_id
            )
            
            if progress_callback:
                progress_callback(camera_name)
                
        except Exception as e:
            # IMPROVEMENT: Enhanced logging trace string providing file source context
            logger.error(
                f"Failed processing {camera_name} ({source_path}): {e}", 
                exc_info=True
            )
            # Fail-safe transition: continue executing remaining network cameras
            continue