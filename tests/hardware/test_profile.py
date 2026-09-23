from image_group.hardware.profile import ConcurrencyPlanner, HardwareProfiler


class FailingProbe:
    def cpu_count(self): raise OSError("blocked")
    def memory(self): raise OSError("blocked")
def test_probe_failure_uses_two_core_eight_gb_defaults():
    profile = HardwareProfiler(FailingProbe()).detect()
    assert (profile.logical_cpus, profile.total_memory_gb, profile.fallback) == (2, 8, True)
    assert ConcurrencyPlanner().plan(profile, "balanced").recognition_workers == 2
def test_low_available_memory_reduces_workers():
    class Probe:
        def cpu_count(self): return 16
        def memory(self): return (32, 1)
    plan = ConcurrencyPlanner().plan(HardwareProfiler(Probe()).detect(), "fast")
    assert plan.recognition_workers == 1

