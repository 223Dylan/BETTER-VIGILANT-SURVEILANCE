from multiprocessing import Queue
from typing import Optional, Tuple

# A simple, shared queue for frame streaming to the API layer.
# This prevents camera processes from needing to import API server components.
stream_queue: Optional[Queue] = None


def initialize_stream_queue():
    """Initializes the global stream queue."""
    global stream_queue
    if stream_queue is None:
        stream_queue = Queue()


def get_stream_queue() -> Queue:
    """Returns the initialized stream queue."""
    if stream_queue is None:
        raise RuntimeError("Stream queue has not been initialized.")
    return stream_queue


def put_frame_in_queue(camera_id: str, frame_bytes: bytes):
    """Puts a frame into the stream queue for the API server to consume."""
    try:
        get_stream_queue().put_nowait((camera_id, frame_bytes))
    except Exception:
        # Queue might be full, which is okay. We just drop the frame.
        pass
