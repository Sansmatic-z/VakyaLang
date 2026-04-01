# वाक् भाषा - घटना लूप (Event Loop)
# Vak Language - Async Event Loop for Coroutine Scheduling
#
# ═══════════════════════════════════════════════════════════════════════════
# Signature: Visionary RM (Raj Mitra) ⚡
# "Async/Await with Sanskrit Semantics" 🔥
# ═══════════════════════════════════════════════════════════════════════════
#
# Month 2-3 Advanced Features: Timer-Based Scheduling
# - set_timeout: Execute callback after delay
# - set_interval: Execute callback repeatedly at interval
# - clear_timeout: Cancel a timer
# - async sleep: Non-blocking sleep
#
# © 2026 Raj Mitra (Visionary RM)

from typing import Any, List, Dict, Optional, Callable
from dataclasses import dataclass
import time
import asyncio


@dataclass
class Timer:
    """
    Async timer for delayed/scheduled execution.
    
    Attributes:
        delay: Delay in seconds before execution
        callback: Function/coroutine to execute
        repeat: If True, timer repeats at interval
        next_fire: Timestamp when timer should next fire
        cancelled: Whether timer was cancelled
    """
    delay: float
    callback: Callable
    repeat: bool = False
    next_fire: float = None
    cancelled: bool = False
    
    def __post_init__(self):
        if self.next_fire is None:
            self.next_fire = time.time() + self.delay
    
    def cancel(self):
        """Cancel the timer."""
        self.cancelled = True
    
    def __repr__(self):
        status = "cancelled" if self.cancelled else f"fires_in_{self.delay}s"
        repeat_str = " (repeating)" if self.repeat else ""
        return f"Timer({status}{repeat_str})"


@dataclass
class Task:
    """
    Represents an async task (coroutine) in the event loop.
    
    Attributes:
        coro: The VakCoroutine to execute
        name: Task name for debugging
        callback: Optional callback when task completes
        cancelled: Whether task was cancelled
    """
    coro: Any  # VakCoroutine
    name: str = ""
    callback: Optional[Callable] = None
    cancelled: bool = False
    
    def __repr__(self):
        status = "cancelled" if self.cancelled else ("done" if self.coro.completed else "running")
        return f"Task({self.name or 'unnamed'}, {status})"


class EventLoop:
    """
    Cooperative multitasking event loop for VakyaLang coroutines.

    Implements:
    - Cooperative scheduling (coroutines yield control at await points)
    - Task management (create, cancel, gather)
    - Timer-based scheduling (set_timeout, set_interval, clear_timeout)
    - Sleep/delay support (non-blocking async sleep)
    - Exception propagation

    Usage:
        loop = EventLoop()
        result = loop.run_until_complete(main_coroutine())
    """

    def __init__(self):
        self.tasks: List[Task] = []
        self.timers: List[Timer] = []
        self.current_task: Optional[Task] = None
        self.stopped = False
        self._task_counter = 0
        self._sleeping_tasks: List[tuple] = []  # (wake_time, task)

    @classmethod
    def current(cls) -> 'EventLoop':
        """Get the current event loop (singleton pattern)."""
        if not hasattr(cls, '_current_loop'):
            cls._current_loop = cls()
        return cls._current_loop

    def create_task(self, coro: Any, name: str = None, callback: Callable = None) -> Task:
        """
        Create a new task from a coroutine.
        
        Args:
            coro: VakCoroutine to schedule
            name: Optional task name
            callback: Optional callback(task) when complete
            
        Returns:
            Created Task object
        """
        task = Task(coro=coro, name=name or f"task-{self._task_counter}", callback=callback)
        self._task_counter += 1
        self.tasks.append(task)
        return task
    
    def run_until_complete(self, coro: Any) -> Any:
        """
        Run until a coroutine completes.
        
        Creates a task for the given coroutine and runs the event loop
        until it (and all spawned tasks) complete.
        
        Args:
            coro: VakCoroutine to run
            
        Returns:
            Result of the coroutine
        """
        # Create main task
        main_task = self.create_task(coro, name="main")
        
        # Run event loop
        while not self.stopped:
            # Check if all tasks are done
            active_tasks = [t for t in self.tasks if not t.cancelled and not t.coro.completed]
            if not active_tasks:
                break
            
            # Run one iteration
            self._run_once()
        
        # Return main task result
        return main_task.coro.result
    
    def _run_once(self):
        """
        Run one iteration of the event loop.

        Executes each active task until it suspends or completes.
        Also processes timers and wakes up sleeping tasks.
        """
        # Process timers first
        self._process_timers()
        
        # Wake up sleeping tasks
        self._process_sleeping_tasks()

        # Get active tasks
        active_tasks = [
            t for t in self.tasks
            if not t.cancelled and not t.coro.completed and not getattr(t.coro, "suspended", False)
        ]

        if not active_tasks:
            return

        # Round-robin scheduling
        for task in active_tasks:
            self.current_task = task
            try:
                self._run_task(task)
            except Exception as e:
                # Task raised exception
                task.coro.completed = True
                task.coro.result = e
                if task.callback:
                    task.callback(task)

        self.current_task = None

    def _process_sleeping_tasks(self):
        """
        Wake up tasks that have finished sleeping.
        """
        now = time.time()
        remaining = []
        for wake_time, task in self._sleeping_tasks:
            if now >= wake_time:
                # Task should wake up
                if task is not None and getattr(task, "coro", None) is not None:
                    task.coro.suspended = False
            else:
                remaining.append((wake_time, task))
        self._sleeping_tasks = remaining
    
    def _run_task(self, task: Task):
        """
        Run a single task until it suspends or completes.
        
        Args:
            task: Task to run
        """
        if task.cancelled or task.coro.completed:
            return
        
        coro = task.coro
        
        # Resume coroutine execution
        from runtime.src.vm import VakVM, SUSPEND
        
        vm = VakVM()
        vm.globals = {}
        vm.builtins = {}
        
        try:
            # Execute single frame until suspend or complete
            result = vm._execute_single_frame(coro.frame)
            
            if result is SUSPEND:
                # Coroutine suspended (hit await)
                coro.suspended = True
            else:
                # Coroutine completed
                coro.completed = True
                coro.result = result
                if task.callback:
                    task.callback(task)
                    
        except Exception as e:
            # Task failed
            coro.completed = True
            coro.result = e
            if task.callback:
                task.callback(task)
    
    def run_forever(self):
        """Run event loop until stopped."""
        self.stopped = False
        while not self.stopped:
            self._run_once()
            # Small sleep to prevent busy-waiting
            time.sleep(0.001)
    
    def stop(self):
        """Stop the event loop."""
        self.stopped = True
    
    def cancel_task(self, task: Task):
        """
        Cancel a task.

        Args:
            task: Task to cancel
        """
        task.cancelled = True

    def set_timeout(self, delay: float, callback: Callable) -> Timer:
        """
        Execute callback after delay (one-shot timer).
        
        Args:
            delay: Delay in seconds
            callback: Function or coroutine to execute
        
        Returns:
            Timer object (can be cancelled with clear_timeout)
        
        Usage:
            def on_timeout():
                print("Timeout!")
            
            timer = loop.set_timeout(2.0, on_timeout)
        """
        timer = Timer(delay, callback, repeat=False)
        self.timers.append(timer)
        return timer

    def set_interval(self, interval: float, callback: Callable) -> Timer:
        """
        Execute callback repeatedly at interval (repeating timer).
        
        Args:
            interval: Interval in seconds between executions
            callback: Function or coroutine to execute
        
        Returns:
            Timer object (can be cancelled with clear_timeout)
        
        Usage:
            counter = 0
            def on_tick():
                nonlocal counter
                counter += 1
                print(f"Tick {counter}")
            
            timer = loop.set_interval(1.0, on_tick)
            # ... later ...
            loop.clear_timeout(timer)
        """
        timer = Timer(interval, callback, repeat=True)
        self.timers.append(timer)
        return timer

    def clear_timeout(self, timer: Timer):
        """
        Cancel a timer.
        
        Args:
            timer: Timer to cancel
        
        Usage:
            timer = loop.set_timeout(5.0, callback)
            # ... changed mind ...
            loop.clear_timeout(timer)
        """
        timer.cancelled = True
        if timer in self.timers:
            self.timers.remove(timer)

    def _process_timers(self):
        """
        Process due timers.
        
        Called each event loop iteration to check and execute
        timers that have fired.
        """
        now = time.time()
        remaining = []
        for timer in self.timers:
            if timer.cancelled:
                continue
            if now >= timer.next_fire:
                # Execute timer callback
                if asyncio.iscoroutinefunction(timer.callback):
                    # Schedule as async task
                    self.create_task(timer.callback())
                else:
                    # Call synchronously
                    timer.callback()
                
                if timer.repeat:
                    # Schedule next fire
                    timer.next_fire = now + timer.delay
                    remaining.append(timer)
                else:
                    # One-shot timers drop out after firing
                    pass
            else:
                remaining.append(timer)
        self.timers = remaining

    def _schedule_sleep(self, wake_time: float, task: Task):
        """
        Schedule a task to wake up at a specific time.
        
        Args:
            wake_time: Unix timestamp when task should wake up
            task: Task to schedule
        """
        self._sleeping_tasks.append((wake_time, task))

    async def _sleep(self, seconds: float):
        """
        Internal async sleep implementation.
        
        Args:
            seconds: Number of seconds to sleep
        
        Returns:
            None when complete
        """
        wake_time = time.time() + seconds
        self._schedule_sleep(wake_time, self.current_task)
        # Suspend will be handled by VM
        from runtime.src.event_loop import SUSPEND
        return SUSPEND

    async def sleep(self, seconds: float) -> Any:
        """
        Sleep for given seconds (async, non-blocking).

        Creates a delay coroutine that suspends execution.

        Args:
            seconds: Number of seconds to sleep

        Returns:
            None when complete
        
        Usage:
            async def main():
                print("Before sleep")
                await EventLoop.sleep(2.0)  # Non-blocking!
                print("After 2 seconds")
        """
        loop = EventLoop.current()
        return await loop._sleep(seconds)
    
    async def gather(self, *coros) -> List[Any]:
        """
        Run multiple coroutines concurrently and gather results.
        
        Args:
            *coros: Coroutines to run
            
        Returns:
            List of results in same order
        """
        tasks = [self.create_task(coro) for coro in coros]
        
        # Wait for all to complete
        while True:
            active = [t for t in tasks if not t.cancelled and not t.coro.completed]
            if not active:
                break
            self._run_once()
        
        # Return results
        results = []
        for task in tasks:
            if isinstance(task.coro.result, Exception):
                raise task.coro.result
            results.append(task.coro.result)
        
        return results


# Sentinel value for suspend
SUSPEND = object()


def run_async(main_coro: Any) -> Any:
    """
    Convenience function to run an async coroutine.
    
    Usage:
        result = run_async(main())
    
    Args:
        main_coro: Coroutine to run
        
    Returns:
        Result of coroutine
    """
    loop = EventLoop()
    return loop.run_until_complete(main_coro)


# Export public API
__all__ = [
    'EventLoop',
    'Task',
    'Timer',
    'run_async',
    'SUSPEND',
]

# Documentation Aliases
VakEventLoop = EventLoop
चलाओ = run_async
