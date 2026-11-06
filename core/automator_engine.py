import time
import re
from typing import List
from core.models import RequestModel, ResponseModel, AutomatorTask
from core.http_engine import HttpEngine
from core.raw_parser import RawHttpParser
from core.qt_compat import QObject, QRunnable, Signal, Slot, QThreadPool


class AutomatorSignals(QObject):
    task_started = Signal(int)
    task_completed = Signal(int, object)
    progress = Signal(int, int)
    finished = Signal()
    stopped = Signal()


class AutomatorTaskWorker(QRunnable):
    def __init__(self, task: AutomatorTask, engine: HttpEngine, signals: AutomatorSignals, delay_ms: int = 0):
        super().__init__()
        self.task = task
        self.engine = engine
        self.signals = signals
        self.delay_ms = delay_ms

    @Slot()
    def run(self):
        if self.delay_ms > 0:
            time.sleep(self.delay_ms / 1000.0)

        self.signals.task_started.emit(self.task.task_id)
        resp = self.engine.execute(self.task.request)
        self.task.response = resp
        self.task.status = "COMPLETED" if resp.status_code > 0 else "ERROR"
        self.signals.task_completed.emit(self.task.task_id, resp)


class AutomatorRunner(QObject):
    def __init__(self, engine: HttpEngine):
        super().__init__()
        self.engine = engine
        self.signals = AutomatorSignals()
        self.tasks: List[AutomatorTask] = []
        self.is_running = False
        self.is_cancelled = False
        self.completed_count = 0
        self.total_count = 0
        self.pool = QThreadPool()
        self.signals.task_completed.connect(self._on_task_done)

    def setup(
        self,
        raw_template: str,
        target_override: str,
        payloads: List[str],
        marker_regex: str = r"§([^§]+)§|\{\{([^\}]+)\}\}",
    ) -> List[AutomatorTask]:
        """
        Generates AutomatorTask instances by replacing markers with each payload.
        """
        self.tasks = []
        self.completed_count = 0
        self.total_count = len(payloads)
        self.is_cancelled = False
        if payloads and not re.search(marker_regex, raw_template):
            raise ValueError("The template must contain a §param§ or {{payload}} marker.")

        for i, payload in enumerate(payloads):
            if re.search(marker_regex, raw_template):
                customized_raw = re.sub(marker_regex, payload, raw_template)
            else:
                customized_raw = raw_template.replace("{{payload}}", payload)

            req = RawHttpParser.parse_request(customized_raw, target_override)
            if req.body:
                customized_raw = RawHttpParser.serialize_request(req, update_content_length=True)
                req = RawHttpParser.parse_request(customized_raw, target_override)

            task = AutomatorTask(
                task_id=i + 1,
                payload=payload,
                request=req,
            )
            self.tasks.append(task)

        return self.tasks

    def start(self, max_concurrency: int = 5, delay_ms: int = 0):
        if not self.tasks:
            self.signals.finished.emit()
            return

        self.is_running = True
        self.is_cancelled = False
        self.completed_count = 0
        self.pool.setMaxThreadCount(max(1, min(max_concurrency, 30)))

        for task in self.tasks:
            if self.is_cancelled:
                break
            worker = AutomatorTaskWorker(task, self.engine, self.signals, delay_ms=delay_ms)
            self.pool.start(worker)

    def _on_task_done(self, task_id: int, resp: ResponseModel):
        self.completed_count += 1
        self.signals.progress.emit(self.completed_count, self.total_count)
        if self.completed_count >= self.total_count or self.is_cancelled:
            self.is_running = False
            self.signals.finished.emit()

    def cancel(self):
        self.is_cancelled = True
        self.is_running = False
        self.pool.clear()
        self.signals.stopped.emit()
