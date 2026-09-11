# Mobile Scheduler

The mobile scheduler uses a preemptive time-sliced core with policy inputs for CPU capacity, cluster class, utilization and thermal headroom.

The scheduler ABI is intentionally independent of ARM vendor topology. Platform discovery supplies CPU capacity and cluster information; the scheduler consumes those normalized values.

Future work includes deadline/latency classes, utilization clamping, per-CPU run queues, interrupt affinity, foreground/background policy, and energy-model integration.
