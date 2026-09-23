from dataclasses import dataclass
import os
import psutil
@dataclass(frozen=True, slots=True)
class HardwareProfile:
    logical_cpus: int; total_memory_gb: int; available_memory_gb: int; fallback: bool
@dataclass(frozen=True, slots=True)
class RuntimePlan:
    decode_workers: int; recognition_workers: int; copy_workers: int; queue_size: int
class SystemProbe:
    def cpu_count(self): return os.cpu_count() or 2
    def memory(self):
        memory = psutil.virtual_memory(); gib = 1024 ** 3
        return max(1, round(memory.total / gib)), max(1, round(memory.available / gib))
class HardwareProfiler:
    def __init__(self, probe=None): self.probe = probe or SystemProbe()
    def detect(self):
        try:
            cpus = max(1, int(self.probe.cpu_count())); total, available = self.probe.memory()
            return HardwareProfile(cpus, int(total), int(available), False)
        except Exception: return HardwareProfile(2, 8, 4, True)
class ConcurrencyPlanner:
    def plan(self, profile: HardwareProfile, mode: str = "balanced") -> RuntimePlan:
        factor = {"eco": .5, "balanced": 1, "fast": 1.5}.get(mode, 1)
        recognition = max(1, min(profile.logical_cpus, round(profile.logical_cpus * factor)))
        if profile.available_memory_gb <= 1: recognition = 1
        decode = max(1, min(4, recognition)); queue = max(2, recognition * 2)
        return RuntimePlan(decode, recognition, 1, queue)

