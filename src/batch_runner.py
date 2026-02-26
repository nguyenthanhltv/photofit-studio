"""Batch processing orchestrator with parallel execution and progress tracking."""

import os
import time
import logging
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Optional, List

from .processor import ImageProcessor
from .utils import scan_images, build_output_filename, ensure_output_dir, format_time

logger = logging.getLogger("image_processor")

class BatchResult:
    """Result container for a single image processing."""

    def __init__(self, input_path: str):
        self.input_path = input_path
        self.output_path: Optional[str] = None
        self.success: bool = False
        self.steps: List[str] = []
        self.error: Optional[str] = None
        self.duration: float = 0.0

class BatchRunner:
    """Orchestrates batch processing of multiple images."""

    def __init__(self, config: dict):
        self.config = config
        self._cancel_event = threading.Event()
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    def cancel(self) -> None:
        """Signal cancellation of current batch."""
        self._cancel_event.set()
        logger.info("Batch cancellation requested")

    def run(
        self,
        input_folder: str,
        output_folder: str,
        input_images: Optional[List[str]] = None,
        on_progress: Optional[Callable] = None,
        on_complete: Optional[Callable] = None,
        on_error: Optional[Callable] = None
    ) -> List[BatchResult]:
        """Run batch processing on all images in input folder.

        Args:
            input_folder: Path to folder containing source images
            output_folder: Path to output folder
            on_progress: Callback(current, total, result) for progress updates
            on_complete: Callback(results) when batch finishes
            on_error: Callback(path, error) for individual image errors

        Returns:
            List of BatchResult objects
        """
        self._cancel_event.clear()
        self._running = True
        results = []

        try:
            images = input_images if input_images is not None else scan_images(input_folder)
            if not images:
                logger.warning(f"No images to process in {input_folder}")
                return results

            ensure_output_dir(output_folder)
            total = len(images)
            logger.info(f"Starting batch: {total} images")

            proc_cfg = self.config.get("processing", {})
            workers = max(1, min(proc_cfg.get("parallel_workers", 4), 8))
            skip_on_error = proc_cfg.get("skip_on_error", True)

            output_cfg = self.config.get("output", {})
            naming = output_cfg.get("naming", "{name}")
            fmt = output_cfg.get("format", "jpg")
            overwrite = output_cfg.get("overwrite", False)

            # Create skipped directory for images without faces
            skipped_dir = os.path.join(output_folder, "_skipped")

            processor = ImageProcessor(self.config)
            completed = 0
            start_time = time.time()

            # Process images using thread pool
            with ThreadPoolExecutor(max_workers=workers) as executor:
                future_map = {}
                for img_path in images:
                    if self._cancel_event.is_set():
                        break
                    future = executor.submit(self._process_single, processor, img_path,
                                             output_folder, skipped_dir, naming, fmt, overwrite)
                    future_map[future] = img_path

                for future in as_completed(future_map):
                    if self._cancel_event.is_set():
                        logger.info("Batch cancelled by user")
                        break

                    img_path = future_map[future]
                    try:
                        result = future.result()
                        results.append(result)

                        if not result.success and on_error:
                            on_error(result.input_path, result.error)

                    except Exception as e:
                        br = BatchResult(img_path)
                        br.error = str(e)
                        results.append(br)
                        logger.error(f"Unexpected error processing {img_path}: {e}")

                        if not skip_on_error:
                            self._cancel_event.set()
                            break

                    completed += 1
                    if on_progress:
                        elapsed = time.time() - start_time
                        on_progress(completed, total, results[-1] if results else None, elapsed)

            processor.close()

            elapsed_total = time.time() - start_time
            success_count = sum(1 for r in results if r.success)
            logger.info(f"Batch complete: {success_count}/{total} succeeded in {format_time(elapsed_total)}")

            if on_complete:
                on_complete(results)

        finally:
            self._running = False

        return results

    def _process_single(
        self,
        processor: ImageProcessor,
        input_path: str,
        output_folder: str,
        skipped_dir: str,
        naming: str,
        fmt: str,
        overwrite: bool
    ) -> BatchResult:
        """Process a single image file.

        Args:
            processor: ImageProcessor instance
            input_path: Source image path
            output_folder: Output directory
            skipped_dir: Directory for skipped images
            naming: Output naming pattern
            fmt: Output format
            overwrite: Allow overwrite

        Returns:
            BatchResult
        """
        result = BatchResult(input_path)
        start = time.time()

        try:
            processed, status = processor.process_file(input_path)
            result.steps = status.get("steps_applied", [])

            if processed is None:
                result.error = status.get("error", "Processing returned None")
                # Copy to skipped folder
                import shutil
                os.makedirs(skipped_dir, exist_ok=True)
                dest = os.path.join(skipped_dir, os.path.basename(input_path))
                shutil.copy2(input_path, dest)
                logger.info(f"Skipped (no face): {input_path} → {dest}")
                return result

            if not status.get("success", False):
                result.error = status.get("error", "Unknown error")
                return result

            # Build output path and save
            out_path = build_output_filename(input_path, naming, fmt, output_folder, overwrite)
            processor.save_result(processed, out_path)

            result.output_path = out_path
            result.success = True
            
            # Record to statistics
            try:
                from .statistics import record_success
                record_success(result.duration)
            except:
                pass
            
            logger.info(f"Processed: {input_path} → {out_path}")

        except Exception as e:
            result.error = str(e)
            logger.error(f"Error processing {input_path}: {e}")

        result.duration = time.time() - start
        return result

    def run_async(
        self,
        input_folder: str,
        output_folder: str,
        input_images: Optional[List[str]] = None,
        on_progress: Optional[Callable] = None,
        on_complete: Optional[Callable] = None,
        on_error: Optional[Callable] = None
    ) -> threading.Thread:
        """Run batch processing in a background thread.

        Returns:
            The running Thread object
        """
        thread = threading.Thread(
            target=self.run,
            args=(input_folder, output_folder, input_images, on_progress, on_complete, on_error),
            daemon=True
        )
        thread.start()
        return thread