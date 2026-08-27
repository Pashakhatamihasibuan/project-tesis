"""
Utility profiling waktu, dipakai speed_benchmark.py untuk mengukur
kontribusi tiap tahap (embedding query, retrieval, generation) terhadap
total waktu respons -- bukan cuma total end-to-end saja. Ini penting
untuk bab pembahasan: kalau HyDE lebih lambat, APAKAH karena tahap
generate-dokumen-hipotesis, atau karena retrieval-nya sendiri yang
lambat? Tanpa breakdown per tahap, pertanyaan ini tidak terjawab.
"""
import time
from contextlib import contextmanager
from dataclasses import dataclass, field


@dataclass
class StageTiming:
    stage_name: str
    duration_seconds: float


@dataclass
class TimingCollector:
    """
    Kumpulkan durasi tiap tahap dalam satu request. Dipakai sebagai:

        collector = TimingCollector()
        with collector.stage("embedding_query"):
            ...
        with collector.stage("retrieval"):
            ...
    """
    stages: list[StageTiming] = field(default_factory=list)

    @contextmanager
    def stage(self, name: str):
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            self.stages.append(StageTiming(stage_name=name, duration_seconds=elapsed))

    @property
    def total_seconds(self) -> float:
        return sum(s.duration_seconds for s in self.stages)

    def as_dict(self) -> dict:
        result = {s.stage_name: round(s.duration_seconds, 4) for s in self.stages}
        result["total"] = round(self.total_seconds, 4)
        return result
