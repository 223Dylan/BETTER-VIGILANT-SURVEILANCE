from abc import ABC, abstractmethod
from typing import Any, Dict
from loguru import logger
from .utils import Config

class BaseComponent(ABC):
    """Base class for all components in the pipeline."""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self._initialized = False
        self._running = False

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the component."""
        pass

    @abstractmethod
    def start(self) -> bool:
        """Start the component."""
        pass

    @abstractmethod
    def stop(self) -> bool:
        """Stop the component."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources."""
        pass

    def is_initialized(self) -> bool:
        """Check if component is initialized."""
        return self._initialized

    def is_running(self) -> bool:
        """Check if component is running."""
        return self._running

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)

    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration values."""
        return self.config.get_all()

    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        self.cleanup() 