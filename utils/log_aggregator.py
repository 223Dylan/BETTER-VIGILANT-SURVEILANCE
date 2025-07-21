import json
import logging
import queue
import socket
import threading
import time
from datetime import datetime
from logging.handlers import HTTPHandler
from typing import Any, Dict, Optional

import requests


class ElasticsearchHandler(logging.Handler):
    """Custom handler that sends logs to Elasticsearch."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 9200,
        index_prefix: str = "camera-system",
        batch_size: int = 100,
        flush_interval: int = 5,
    ):
        super().__init__()
        self.host = host
        self.port = port
        self.index_prefix = index_prefix
        self.batch_size = batch_size
        self.flush_interval = flush_interval

        # Create queue for batching
        self.queue = queue.Queue()
        self.batch: list = []

        # Start background thread for processing
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._process_queue)
        self._thread.daemon = True
        self._thread.start()

    def _get_index_name(self) -> str:
        """Get the index name based on date."""
        return f"{self.index_prefix}-{datetime.now().strftime('%Y.%m.%d')}"

    def _process_queue(self):
        """Process queued logs in batches."""
        last_flush = time.time()

        while not self._stop_event.is_set():
            try:
                # Get log entry from queue with timeout
                try:
                    log_entry = self.queue.get(timeout=1)
                    self.batch.append(log_entry)
                except queue.Empty:
                    pass

                # Check if we should flush
                current_time = time.time()
                if len(self.batch) >= self.batch_size or (
                    self.batch and current_time - last_flush >= self.flush_interval
                ):
                    self._flush_batch()
                    last_flush = current_time

            except Exception as e:
                print(f"Error processing log queue: {e}")

    def _flush_batch(self):
        """Flush the current batch to Elasticsearch."""
        if not self.batch:
            return

        try:
            # Prepare bulk request
            bulk_data = []
            for log_entry in self.batch:
                # Add index action
                bulk_data.append({"index": {"_index": self._get_index_name()}})
                # Add log document
                bulk_data.append(log_entry)

            # Send to Elasticsearch
            url = f"http://{self.host}:{self.port}/_bulk"
            response = requests.post(
                url,
                data="\n".join(json.dumps(item) for item in bulk_data) + "\n",
                headers={"Content-Type": "application/x-ndjson"},
            )
            response.raise_for_status()

            # Clear batch
            self.batch.clear()

        except Exception as e:
            print(f"Error flushing log batch: {e}")

    def emit(self, record: logging.LogRecord):
        """Emit a log record to the queue."""
        try:
            # Create log entry
            log_entry = {
                "@timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
                "hostname": socket.gethostname(),
                "process_id": record.process,
                "thread_id": record.thread,
                "thread_name": record.threadName,
            }

            # Add extra fields
            if hasattr(record, "extra"):
                log_entry.update(record.extra)

            # Add exception info
            if record.exc_info:
                log_entry["exception"] = self.formatException(record.exc_info)

            # Add to queue
            self.queue.put(log_entry)

        except Exception as e:
            print(f"Error emitting log record: {e}")

    def close(self):
        """Close the handler and flush remaining logs."""
        self._stop_event.set()
        self._thread.join()
        self._flush_batch()


def setup_log_aggregation(
    host: str = "localhost",
    port: int = 9200,
    index_prefix: str = "camera-system",
    batch_size: int = 100,
    flush_interval: int = 5,
) -> ElasticsearchHandler:
    """
    Set up log aggregation to Elasticsearch.

    Args:
        host: Elasticsearch host
        port: Elasticsearch port
        index_prefix: Prefix for index names
        batch_size: Number of logs to batch before sending
        flush_interval: Seconds between batch flushes

    Returns:
        Configured ElasticsearchHandler
    """
    handler = ElasticsearchHandler(
        host=host,
        port=port,
        index_prefix=index_prefix,
        batch_size=batch_size,
        flush_interval=flush_interval,
    )
    return handler


# Global handler instance
elasticsearch_handler: Optional[ElasticsearchHandler] = None


def init_log_aggregation(
    host: str = "localhost", port: int = 9200, index_prefix: str = "camera-system"
) -> ElasticsearchHandler:
    """Initialize the log aggregator."""
    global elasticsearch_handler
    if elasticsearch_handler is None:
        elasticsearch_handler = setup_log_aggregation(
            host=host, port=port, index_prefix=index_prefix
        )
    return elasticsearch_handler


def get_log_aggregator() -> ElasticsearchHandler:
    """Get the global log aggregator instance."""
    if elasticsearch_handler is None:
        raise RuntimeError(
            "Log aggregation not initialized. Call init_log_aggregation first."
        )
    return elasticsearch_handler
