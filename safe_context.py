#!/usr/bin/env python3

"""
SafeContext - A robust wrapper for MCP context objects
This module handles missing attributes gracefully and provides fallbacks
"""

import logging
from typing import Optional, Any, Union

class SafeContext:
    """Safe context wrapper that handles missing attributes gracefully."""
    
    def __init__(self, ctx=None):
        self.ctx = ctx
        self.logger = logging.getLogger("SafeContext")
    
    async def progress(self, message: Optional[str] = None, current: Optional[int] = None, total: int = 100) -> bool:
        """
        Safely report progress, with fallbacks for different context APIs.
        
        Args:
            message: Progress message to display
            current: Current progress value
            total: Total progress value (default: 100)
            
        Returns:
            bool: True if progress was reported, False otherwise
        """
        if message:
            self.logger.info(f"Progress: {message}")
            
        if self.ctx is None:
            return True
            
        try:
            # Try different progress reporting methods based on available attributes
            if hasattr(self.ctx, 'report_progress'):
                if current is not None:
                    await self.ctx.report_progress(current, total)
                else:
                    await self.ctx.report_progress(message=message)
                return True
            elif hasattr(self.ctx, 'progress'):
                if current is not None:
                    self.ctx.progress(current, total)
                else:
                    self.ctx.progress(message)
                return True
            else:
                # No progress method available, log locally
                return True
        except Exception as e:
            self.logger.warning(f"Error reporting progress: {e}")
            return False
    
    async def log(self, level: str, message: str) -> None:
        """
        Log a message using the appropriate context method or fallback to local logging.
        
        Args:
            level: Log level (info, error, warning, debug)
            message: Log message
        """
        # Always log locally first
        if level == "info":
            self.logger.info(message)
        elif level == "error":
            self.logger.error(message)
        elif level == "warning":
            self.logger.warning(message)
        elif level == "debug":
            self.logger.debug(message)
        
        if self.ctx is None:
            return
            
        try:
            # Try to use the appropriate context method
            if level == "info" and hasattr(self.ctx, "info"):
                await self.ctx.info(message)
            elif level == "error" and hasattr(self.ctx, "error"):
                await self.ctx.error(message)
            elif level == "warning" and hasattr(self.ctx, "warning"):
                await self.ctx.warning(message)
            elif level == "debug" and hasattr(self.ctx, "debug"):
                await self.ctx.debug(message)
            elif hasattr(self.ctx, "log"):
                # Fallback to generic log method
                await self.ctx.log(level, message)
        except Exception as e:
            self.logger.warning(f"Error when using context.{level}(): {e}")
    
    async def info(self, message: str) -> None:
        """Log an info message."""
        await self.log("info", message)
    
    async def error(self, message: str) -> None:
        """Log an error message."""
        await self.log("error", message)
    
    async def warning(self, message: str) -> None:
        """Log a warning message."""
        await self.log("warning", message)
    
    async def debug(self, message: str) -> None:
        """Log a debug message."""
        await self.log("debug", message)
    
    async def success(self, message: str) -> None:
        """Log a success message (using info level)."""
        await self.log("info", f"✅ {message}")
