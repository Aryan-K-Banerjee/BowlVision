# core/cv/tag_events.py
'''--------------------------------------------------------------------------
This module contains function to tag events by tagging frames in a video using
an OpenCV window.

Events to be tagged:
- Jump
- BFC
- FFC
- Release

UI:
- The window should open in full screen
- There should be a title saying Back View or Side View based on the video
- The instructions for controls should be displayed under the title 
- The video should be displayed in the rest of the screen without being resized, 
but with black borders if necessary, and fitting within the screen resolution.
- The video should play normally.


Controls:
- Space: Play/Pause
- Left Arrow: Previous Frame
- Right Arrow: Next Frame
- A scrollbar to navigate through the video
- 1: Jump
- 2: BFC
- 3: FFC
- 4: Release
- s: Save and continue
- q: Exit without saving

UI wise, it does not have to be spectacular, but it should be functional, have clear
instructions on the window, 

The tagged events should be saved in a JSON file with the following format:
"video": {
    "view" : "back" or "side",
    "file_location": "path/to/video.mp4",
    "events": {
        "jump": {"frame": frame_number, "time": time_stamp},
        "bfc": {"frame": frame_number, "time": time_stamp},
        "ffc": {"frame": frame_number, "time": time_stamp},
        "release": {"frame": frame_number, "time": time_stamp}
    }
}
-------------------------------------------------------------------------'''
import os
import json
import cv2
import time
import numpy as np
from typing import Dict, Optional
import ctypes


# The main function to tag events in a video
'''
Codes:
    "EVENTS_TAGGED"
    "NO_VIDEO"
    "ERROR"
'''
def tag_events(video_name: str, video_exists: bool, video_location: str, events_location: str) -> None:
    """Wrapper for event tagging UI.

    This function prints minimal status messages and delegates the
    interactive OpenCV tagging work to `_open_tagging_window`.
    It intentionally does not return status codes.
    """
    if not video_exists:
        print(f"NO {video_name}")
        return

    print(f"Starting tagging for video: {video_name}")
    try:
        saved = _open_tagging_window(video_location, events_location, video_name)
        if saved:
            print(f"Tagged successfully: {video_name}")
    except Exception:
        print("Error tagging video")


def _open_tagging_window(video_location: str, events_location: str, video_name: str) -> bool:
    """Run the OpenCV UI to tag events.

    Returns True if events were saved, False if cancelled or video missing.
    Raises exceptions for unexpected errors.
    """
    # validate video file exists
    if not os.path.exists(video_location):
        return False

    cap = None
    try:
        cap = cv2.VideoCapture(video_location)
        if not cap.isOpened():
            return False

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0

        # determine view name from the supplied video name (use name for UI instead of full path)
        lower = video_name.lower()
        if "back" in lower:
            view = "back"
            title = "Back View"
        elif "side" in lower:
            view = "side"
            title = "Side View"
        else:
            view = "unknown"
            title = "Video"

        events: Dict[str, Optional[Dict[str, float]]] = {
            "jump": None,
            "bfc": None,
            "ffc": None,
            "release": None,
        }

        window_name = f"Tag Events - {title}"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

        # determine screen size (attempt Windows API first), fallback to 1280x720
        def _get_screen_size():
            try:
                user32 = ctypes.windll.user32
                # ensure correct DPI scaling on Windows
                try:
                    user32.SetProcessDPIAware()
                except Exception:
                    pass
                return int(user32.GetSystemMetrics(0)), int(user32.GetSystemMetrics(1))
            except Exception:
                return 1280, 720

        screen_w, screen_h = _get_screen_size()
        # reserve a top area for UI overlay
        ui_height = 80
        # resize the window to screen size (will work on most platforms)
        try:
            cv2.resizeWindow(window_name, screen_w, screen_h)
        except Exception:
            try:
                cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            except Exception:
                pass

        paused = False
        current_frame_idx = 0
        save_feedback = None  # (timestamp, message)

        def set_frame_from_trackbar(pos):
            nonlocal current_frame_idx
            current_frame_idx = int(pos)
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame_idx)

        # create a trackbar for navigation
        cv2.createTrackbar('pos', window_name, 0, max(0, total_frames - 1), set_frame_from_trackbar)

        while True:
            if not paused:
                # read current frame
                cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame_idx)
                ret, frame = cap.read()
                if not ret:
                    # reached end
                    paused = True
                    frame = None
            else:
                # when paused, just grab the frame at current position
                cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame_idx)
                ret, frame = cap.read()
                if not ret:
                    frame = None

            # prepare display background
            bg = np.zeros((screen_h, screen_w, 3), dtype=np.uint8)

            if frame is not None:
                fh, fw = frame.shape[:2]
                # compute scale to fit frame into available area while preserving aspect ratio
                avail_w = screen_w
                avail_h = max(1, screen_h - ui_height)
                scale = min(avail_w / fw, avail_h / fh)
                new_w = max(1, int(fw * scale))
                new_h = max(1, int(fh * scale))
                resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR)
                # center the resized frame in the available area below the UI
                x = (screen_w - new_w) // 2
                y = ui_height + (avail_h - new_h) // 2
                bg[y:y+new_h, x:x+new_w] = resized
            else:
                # no frame available, leave black background
                pass

            display = bg
            h, w = display.shape[:2]
            # overlay UI text
            overlay_text = f"{title}   Frame: {current_frame_idx+1}/{max(1,total_frames)}   FPS: {fps:.1f}"
            instr = "Space:Play/Pause  <-/->:Frame  1:Jump 2:BFC 3:FFC 4:Release  s:Save  q:Quit"
            cv2.rectangle(display, (0, 0), (w, 60), (0, 0, 0), -1)
            cv2.putText(display, overlay_text, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(display, instr, (10, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

            # draw currently tagged events
            y = 80
            for k, v in events.items():
                text = f"{k}: " + (f"frame={v['frame']} time={v['time']:.3f}s" if v else "-")
                cv2.putText(display, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0) if v else (100, 100, 100), 1)
                y += 20

            # draw save feedback if present (for 1 second)
            if save_feedback is not None:
                ts, msg = save_feedback
                if time.time() - ts < 1.0:
                    fh = 30
                    cv2.rectangle(display, (w - 220, 10), (w - 10, 10 + fh), (0, 0, 0), -1)
                    cv2.putText(display, msg, (w - 210, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0) if msg == "Saved" else (0, 0, 255), 2)
                else:
                    save_feedback = None

            # show
            cv2.imshow(window_name, display)
            cv2.setTrackbarPos('pos', window_name, min(current_frame_idx, max(0, total_frames - 1)))

            raw_key = cv2.waitKey(0 if paused else int(1000 / max(1.0, fps)))
            # raw_key == -1 means no key was pressed during the timeout
            if raw_key == -1:
                # no key: when playing, we'll advance the frame below; when paused, nothing to do
                masked = None
            else:
                masked = raw_key & 0xFF

            # process keys only when a key was actually pressed
            if masked is not None:
                # common key checks use the masked (0-255) value
                if masked == ord(' '):
                    paused = not paused
                elif masked in (ord('q'), ord('Q')):
                    # cancel: exit without saving
                    return False
                elif masked in (ord('s'), ord('S')):
                    # final save: only allow if all 4 events are tagged
                    if not all(v is not None for v in events.values()):
                        save_feedback = (time.time(), "Tag all 4 events before saving")
                        print("Save blocked: not all events tagged")
                    else:
                        # save using the supplied video name as the file location in the JSON
                        saved = _save_events(events, video_name, events_location, view)
                        save_feedback = (time.time(), "Saved" if saved else "Save failed")
                        print(f"Save attempted: {events_location} -> {saved}")
                        # show feedback briefly so user sees confirmation
                        try:
                            cv2.imshow(window_name, display)
                            cv2.waitKey(700)
                        except Exception:
                            pass
                        return bool(saved)
                elif masked == ord('1'):
                    _tag_event(events, 'jump', current_frame_idx, cap, fps)
                elif masked == ord('2'):
                    _tag_event(events, 'bfc', current_frame_idx, cap, fps)
                elif masked == ord('3'):
                    _tag_event(events, 'ffc', current_frame_idx, cap, fps)
                elif masked == ord('4'):
                    _tag_event(events, 'release', current_frame_idx, cap, fps)
                elif masked in (ord('a'), ord('A')):
                    # step one frame backward (also pause)
                    current_frame_idx = max(0, current_frame_idx - 1)
                    paused = True
                elif masked in (ord('d'), ord('D')):
                    # step one frame forward (also pause)
                    current_frame_idx = min(max(0, total_frames - 1), current_frame_idx + 1)
                    paused = True
                else:
                    # arrow keys and special keys may return larger values depending on platform
                    # check raw_key for platform-specific arrow codes (Windows/Linux/Mac variations)
                    left_codes = {81, 2424832, 65361}
                    right_codes = {83, 2555904, 65363}
                    if raw_key in left_codes or masked in left_codes:
                        current_frame_idx = max(0, current_frame_idx - 1)
                        paused = True
                    elif raw_key in right_codes or masked in right_codes:
                        current_frame_idx = min(max(0, total_frames - 1), current_frame_idx + 1)
                        paused = True
                    elif raw_key == 27 or masked == 27:  # ESC
                        # treat ESC as cancel (no save)
                        return False

            # when playing, advance frame index
            if not paused:
                current_frame_idx = min(total_frames - 1, current_frame_idx + 1)

        # if we ever exit the loop without an explicit save/cancel, just return False
        return False

    finally:
        # always attempt to release the capture and destroy windows
        try:
            if cap is not None:
                try:
                    cap.release()
                except Exception:
                    pass
        except Exception:
            pass
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass


def _tag_event(events: Dict[str, Optional[Dict[str, float]]], key: str, frame_idx: int, cap, fps: float):
    """Record an event at current frame index and timestamp in seconds."""
    # frame_idx is 0-based; convert to 1-based frame number for human readability
    time_sec = frame_idx / max(1.0, fps)
    events[key] = {"frame": int(frame_idx), "time": float(time_sec)}


def _save_events(events: Dict[str, Optional[Dict[str, float]]], video_location: str, events_location: str, view: str) -> bool:
    try:
        out = {
            "video": {
                "view": view,
                "file_location": video_location,
                "events": {},
            }
        }
        for k, v in events.items():
            if v is not None:
                out["video"]["events"][k] = {"frame": int(v["frame"]), "time": float(v["time"])}

        # ensure directory exists
        dirpath = os.path.dirname(events_location)
        if dirpath and not os.path.exists(dirpath):
            os.makedirs(dirpath, exist_ok=True)

        with open(events_location, 'w', encoding='utf-8') as f:
            json.dump(out, f, indent=4)
        return True
    except Exception:
        return False