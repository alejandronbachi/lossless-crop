# =============================================================================
# CropExecutionController — moves the blocking crop call off the UI thread
# =============================================================================
from __future__ import annotations

from PyQt6.QtCore import QObject, QRunnable, Qt, QThreadPool, pyqtSignal, pyqtSlot


class CropWorkerSignals(QObject):
    """QRunnable can't emit signals directly (it isn't a QObject), so the
    worker owns one of these and emits through it."""

    finished = pyqtSignal(bool, str, str)  # success, output_filepath, error_message


class CropWorker(QRunnable):
    """Executes exactly one crop operation — lossless jpegtran subprocess OR
    Pillow crop — on a QThreadPool worker thread instead of the GUI thread.
    """

    #  UPDATED WORKER INIT TO TAKE RAW DATA PASSES
    def __init__(
        self,
        image_manager,
        lossless: bool,
        source_path,
        output_path,
        source_rect,
        image_dimensions,
        rotation_angle: int = 0,
        is_true_jpeg: bool = False,
    ):
        super().__init__()
        self.image_manager = image_manager
        self.lossless = lossless
        self.source_path = source_path
        self.output_path = output_path
        self.source_rect = source_rect
        self.image_dimensions = image_dimensions
        self.rotation_angle = rotation_angle
        self.is_true_jpeg = is_true_jpeg
        self.signals = CropWorkerSignals()

    @pyqtSlot()
    def run(self) -> None:
        try:
            #  BACKGROUND THREAD NOW DELEGATES DIRECTLY TO THE PROCESSOR ROUTER
            success = self.image_manager.process_and_route_crop(
                lossless=self.lossless,
                source_path=self.source_path,
                output_path=self.output_path,
                source_rect=self.source_rect,
                image_dimensions=self.image_dimensions,
                rotation_angle=self.rotation_angle,
                is_true_jpeg=self.is_true_jpeg,
            )
            self.signals.finished.emit(bool(success), str(self.output_path), "")
        except (
            Exception
        ) as exc:  # subprocess/PIL failures land here, not on the GUI thread
            self.signals.finished.emit(False, str(self.output_path), str(exc))


class CropExecutionController(QObject):
    """Owns the QThreadPool and dispatches crop jobs. LossLessCropApp holds one
    instance (created in __init__) and calls submit_crop(...) instead of
    calling image_manager's crop methods directly from an event handler.

    IMPORTANT: CropWorker.signals.finished is emitted from the worker thread.
    PyQt only auto-marshals a signal onto the receiver's thread when the
    receiver is a QObject slot AND the connection resolves to Queued — a
    signal connected straight to a plain Python closure runs synchronously
    on the EMITTING thread, which would mean UI-touching callbacks (widget
    setChecked/setGeometry calls, etc.) executing off the GUI thread. To
    avoid that, every worker's finished signal is relayed through this
    QObject's own `_crop_finished` signal, which is explicitly connected
    with Qt.ConnectionType.QueuedConnection — since this controller is
    constructed on (and never moved off) the GUI thread, that queued
    connection guarantees `_dispatch_on_main_thread` — and therefore the
    caller-supplied `on_finished` callback — runs on the GUI thread.
    """

    _crop_finished = pyqtSignal(
        object, object, bool, str, str
    )  # worker, on_finished, success, output_path, error

    def __init__(self, image_manager, max_concurrent_jobs: int = 1, parent=None):
        super().__init__(parent)
        self.image_manager = image_manager
        self.pool = QThreadPool()
        self.pool.setMaxThreadCount(max_concurrent_jobs)
        self._active_workers: list = []  # only ever mutated on the GUI thread
        self._crop_finished.connect(
            self._dispatch_on_main_thread, Qt.ConnectionType.QueuedConnection
        )

    def submit_crop(
        self,
        lossless: bool,
        source_path,
        output_path,
        source_rect,
        image_dimensions,
        on_finished,
        rotation_angle: int = 0,
        is_true_jpeg: bool = False,
    ) -> None:
        """on_finished: callable(success: bool, output_filepath: str, error_message: str),
        guaranteed to run on the GUI thread."""

        # Worker now wraps the raw data structures directly without processing them here
        worker = CropWorker(
            self.image_manager,
            lossless,
            source_path,
            output_path,
            source_rect,
            image_dimensions,
            rotation_angle=rotation_angle,
            is_true_jpeg=is_true_jpeg,
        )
        self._active_workers.append(worker)

        def _relay(success: bool, output_filepath: str, error_message: str):
            # Runs on the worker thread; only touches this signal, nothing UI-related.
            self._crop_finished.emit(
                worker, on_finished, success, output_filepath, error_message
            )

        worker.signals.finished.connect(_relay)
        self.pool.start(worker)

    @pyqtSlot(object, object, bool, str, str)
    def _dispatch_on_main_thread(
        self, worker, on_finished, success, output_filepath, error_message
    ):
        if worker in self._active_workers:
            self._active_workers.remove(worker)
        on_finished(success, output_filepath, error_message)

    def has_pending_jobs(self) -> bool:
        """Guard against double-submission (e.g. a fast double-tap of Space)
        racing two writes to the same output path."""
        return len(self._active_workers) > 0

    def wait_for_all(self, timeout_ms: int = 5000) -> bool:
        """Call from closeEvent so an in-flight jpegtran subprocess isn't
        killed mid-write when the app exits."""
        return self.pool.waitForDone(timeout_ms)
