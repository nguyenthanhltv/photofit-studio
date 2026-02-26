"""GPU acceleration utilities for PhotoFit Studio.

Provides GPU detection and OpenCV CUDA support.
"""

import os
import logging
from typing import Optional, Tuple

logger = logging.getLogger("gpu_accelerator")

# GPU detection results
_gpu_available = None
_cuda_available = None


def is_gpu_available() -> bool:
    """Check if GPU is available for processing.
    
    Returns:
        True if GPU is available
    """
    global _gpu_available
    
    if _gpu_available is not None:
        return _gpu_available
    
    _gpu_available = False
    
    # Check for CUDA
    try:
        import cv2
        cuda_info = cv2.getBuildInformation()
        if "CUDA" in cuda_info:
            lines = cuda_info.split("\n")
            for line in lines:
                if "CUDA" in line and "YES" in line:
                    _gpu_available = True
                    logger.info("CUDA GPU detected")
                    break
    except:
        pass
    
    # Check for OpenCL (AMD/Intel GPUs)
    try:
        import cv2
        ocl_info = cv2.getBuildInformation()
        if "OpenCL" in ocl_info:
            lines = ocl_info.split("\n")
            for line in lines:
                if "OpenCL" in line and "YES" in line:
                    _gpu_available = True
                    logger.info("OpenCL support detected")
                    break
    except:
        pass
    
    if not _gpu_available:
        logger.info("No GPU detected, using CPU")
    
    return _gpu_available


def get_device_info() -> dict:
    """Get GPU device information.
    
    Returns:
        Dict with device info
    """
    info = {
        "gpu_available": is_gpu_available(),
        "cuda_available": is_cuda_available(),
        "opencl_available": is_opencl_available(),
        "device_name": "CPU",
        "device_count": 1
    }
    
    try:
        import cv2
        build_info = cv2.getBuildInformation()
        
        # Parse CUDA info
        if "CUDA" in build_info:
            lines = build_info.split("\n")
            in_cuda_section = False
            for line in lines:
                if "CUDA" in line:
                    in_cuda_section = True
                if in_cuda_section and "Name" in line:
                    info["device_name"] = line.split(":")[-1].strip()
                    break
    except:
        pass
    
    return info


def is_cuda_available() -> bool:
    """Check if CUDA is available.
    
    Returns:
        True if CUDA is available
    """
    global _cuda_available
    
    if _cuda_available is not None:
        return _cuda_available
    
    _cuda_available = False
    
    try:
        import cv2
        cuda_info = cv2.getBuildInformation()
        if "CUDA" in cuda_info:
            lines = cuda_info.split("\n")
            for line in lines:
                if "CUDA" in line and "YES" in line:
                    _cuda_available = True
                    break
    except:
        pass
    
    return _cuda_available


def is_opencl_available() -> bool:
    """Check if OpenCL is available.
    
    Returns:
        True if OpenCL is available
    """
    global _cuda_available
    
    # Already checked
    if _cuda_available:
        return True
    
    try:
        import cv2
        ocl_info = cv2.getBuildInformation()
        if "OpenCL" in ocl_info:
            lines = ocl_info.split("\n")
            for line in lines:
                if "OpenCL" in line and "YES" in line:
                    return True
    except:
        pass
    
    return False


def get_optimal_workers() -> int:
    """Get optimal number of workers based on hardware.
    
    Returns:
        Optimal worker count
    """
    import multiprocessing
    
    cpu_count = multiprocessing.cpu_count()
    
    if is_gpu_available():
        # GPU can handle more parallel workers
        return min(cpu_count, 8)
    else:
        # CPU-only, use fewer workers to avoid memory issues
        return min(cpu_count - 1, 4)


def suggest_processing_settings() -> dict:
    """Suggest optimal processing settings based on hardware.
    
    Returns:
        Dict with suggested settings
    """
    gpu_available = is_gpu_available()
    
    settings = {
        "use_gpu": gpu_available,
        "parallel_workers": get_optimal_workers(),
        "batch_size": 4 if gpu_available else 2,
        "enable_super_resolution": gpu_available,  # Only with GPU
        "enable_face_restoration": gpu_available,  # Only with GPU
        "memory_efficient": not gpu_available,
    }
    
    if gpu_available:
        settings["description"] = "GPU-accelerated processing enabled"
    else:
        settings["description"] = "CPU processing (GPU not available)"
    
    return settings


class GPUContext:
    """Context manager for GPU operations."""
    
    def __init__(self):
        self._device = None
        self._original_device = None
    
    def __enter__(self):
        """Set up GPU context."""
        if is_gpu_available():
            try:
                import cv2
                # Try to use CUDA
                self._original_device = cv2.cuda.getDevice()
                self._device = 0
                cv2.cuda.setDevice(self._device)
                logger.info(f"GPU context set: device {self._device}")
            except:
                logger.warning("Could not set GPU context")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up GPU context."""
        if self._device is not None:
            try:
                import cv2
                cv2.cuda.resetDevice()
            except:
                pass


def get_backend_info() -> dict:
    """Get detailed backend information.
    
    Returns:
        Dict with backend details
    """
    info = {
        "opencv_version": "unknown",
        "cuda_version": None,
        "cudnn_version": None,
        "opencl_version": None,
    }
    
    try:
        import cv2
        info["opencv_version"] = cv2.__version__
        
        build_info = cv2.getBuildInformation()
        
        # Parse various versions
        lines = build_info.split("\n")
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if "CUDA" in line:
                current_section = "CUDA"
            elif "OpenCL" in line:
                current_section = "OpenCL"
            elif "cuDNN" in line:
                current_section = "cuDNN"
            
            if current_section and ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                
                if current_section == "CUDA" and "Version" in key:
                    info["cuda_version"] = value
                elif current_section == "cuDNN" and "Version" in key:
                    info["cudnn_version"] = value
                elif current_section == "OpenCL" and "Version" in key:
                    info["opencl_version"] = value
                    
    except Exception as e:
        logger.error(f"Error getting backend info: {e}")
    
    return info


# Performance monitoring
class PerformanceMonitor:
    """Monitor processing performance."""
    
    def __init__(self):
        self._times = {}
        self._counts = {}
    
    def start(self, name: str):
        """Start timing an operation."""
        import time
        self._times[name] = {"start": time.time()}
    
    def end(self, name: str):
        """End timing an operation."""
        import time
        if name in self._times and "start" in self._times[name]:
            elapsed = time.time() - self._times[name]["start"]
            if name not in self._counts:
                self._counts[name] = {"count": 0, "total_time": 0}
            self._counts[name]["count"] += 1
            self._counts[name]["total_time"] += elapsed
    
    def get_stats(self, name: str) -> dict:
        """Get statistics for an operation."""
        if name not in self._counts:
            return {"count": 0, "avg_time": 0, "total_time": 0}
        
        count = self._counts[name]["count"]
        total = self._counts[name]["total_time"]
        return {
            "count": count,
            "total_time": total,
            "avg_time": total / count if count > 0 else 0
        }
    
    def get_all_stats(self) -> dict:
        """Get all statistics."""
        return {name: self.get_stats(name) for name in self._counts}
    
    def reset(self):
        """Reset all statistics."""
        self._times = {}
        self._counts = {}


# Global performance monitor
_perf_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor."""
    return _perf_monitor
