# 187. `fork()` in a Multi-Threaded Process (BUMPS/DREAM)

**Priority:** `[priority] medium`

**Type:** Forward-compatibility / Concurrency

The test suite emits, on Python 3.12+ (seen on 3.12 and 3.14):

```
multiprocessing/popen_fork.py: DeprecationWarning: This process is
multi-threaded, use of fork() may lead to deadlocks in the child.
  self.pid = os.fork()
```

It fires whenever BUMPS/DREAM starts worker processes via the default
`fork` start method while the process already has live threads. Seen in:

- unit: `tests/unit/easydiffraction/analysis/minimizers/test_bumps_dream.py::test_run_solver_preserves_parameter_order_and_forwards_init`
- integration: `tests/integration/fitting/test_bumps_dream_support.py::test_run_solver_preserves_parameter_order_and_forwards_init`
  and the DREAM resume tests.

This is not just log noise: Python is hardening fork-while-threaded
(slated to change the default start method), and fork in a multi-threaded
parent genuinely risks child-process deadlocks — exactly the
`MPMapper` startup path EasyDiffraction drives.

**Tension with issue 95.** Issue 95 (Re-Enable DREAM Multiprocessing)
proposes *preferring* a `fork` context for direct-script entry points.
That recommendation must be reconciled with this warning: the chosen
multiprocessing policy needs to be safe for fork-while-threaded (or use
`forkserver`/`spawn` with import-safe workers), not just fast.

**Fix:** decide and document an explicit multiprocessing start-method
policy for the Bayesian backends that is safe under Python's
fork-while-threaded deprecation (e.g. `forkserver`, or `spawn` with
import-safe worker entry points), and align issue 95's solution with it.

**Depends on:** related to issue 95 (multiprocessing start-method policy).
