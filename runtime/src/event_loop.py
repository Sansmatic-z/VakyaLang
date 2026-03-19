# वाक् भाषा - घटना-लूप (Event Loop)
# Vak Language - Async Event Loop
#
# Implements cooperative multitasking for VakyaLang coroutines.
# Uses a run-to-completion model for synchronous execution,
# with proper suspension support for async scheduling.
#
# Usage:
#     लूप = घटना_लूप()
#     लूप.चलाओ(मुख्य_कोरूटीन())
#
# Or in VakyaLang:
#     async def मुख्य():
#         प्रतीक्षा कार्य_१()
#         प्रतीक्षा कार्य_२()
#     
#     चलाओ(मुख्य())

from typing import Any, List, Optional, Tuple, Callable
from collections import deque
import time
from .vm import VakVM, VakCoroutine, VMError


class VakPendingTask:
    """Represents a pending task (timer, I/O, etc.)."""
    def __init__(self, coroutine: VakCoroutine, wake_time: float = None, 
                 callback: Callable = None, io_data: Any = None):
        self.coroutine = coroutine
        self.wake_time = wake_time  # For timers
        self.callback = callback    # For I/O completion
        self.io_data = io_data      # I/O data buffer
    
    def __repr__(self):
        if self.wake_time:
            return f"VakPendingTask({self.coroutine.name}, wake={self.wake_time})"
        return f"VakPendingTask({self.coroutine.name}, callback={self.callback})"


class VakEventLoop:
    """
    Async event loop for VakyaLang coroutines.
    
    Manages execution of multiple coroutines concurrently.
    Uses cooperative multitasking - coroutines yield control at await points.
    
    Architecture:
    - Ready queue: Coroutines ready to run (FIFO)
    - Pending queue: Coroutines waiting on timers or I/O
    - Current: Currently executing coroutine
    
    Scheduling Policy:
    - Run-to-completion between yield points
    - Fair scheduling (FIFO for ready coroutines)
    - Timer-based wake-up for pending coroutines
    
    Usage:
        vm = VakVM()
        loop = VakEventLoop(vm)
        
        # Create main coroutine
        main_coro = vm.create_coroutine(main_func, args)
        
        # Run to completion
        result = loop.run(main_coro)
    """
    
    def __init__(self, vm: VakVM = None):
        """Initialize event loop with optional VM instance."""
        self.vm = vm or VakVM()
        self.ready = deque()      # Coroutines ready to run
        self.pending = []         # Coroutines waiting on I/O or timers
        self.current = None       # Currently running coroutine
        self.stopped = False
        self.task_counter = 0     # For debugging/tracing
    
    def run(self, main_coroutine: VakCoroutine) -> Any:
        """
        Run the event loop until main coroutine completes.
        
        This is the entry point for async execution.
        Executes all scheduled coroutines until the main one finishes.
        
        Args:
            main_coroutine: The main coroutine to execute
            
        Returns:
            The result of the main coroutine
        """
        self.ready.append(main_coroutine)
        
        while self.ready or self.pending:
            if self.stopped:
                break
            
            # Run all ready coroutines
            while self.ready:
                coro = self.ready.popleft()
                completed = self._run_coroutine(coro)
                
                # If not completed and not suspended, re-queue
                if not completed and not coro.suspended:
                    self.ready.append(coro)
            
            # Handle pending coroutines (timers, I/O)
            if self.pending:
                self._handle_pending()
        
        # Return result of main coroutine
        return main_coroutine.result if main_coroutine.completed else None
    
    def _run_coroutine(self, coro: VakCoroutine) -> bool:
        """
        Run a coroutine until it yields (awaits) or completes.
        
        Args:
            coro: The coroutine to execute
            
        Returns:
            True if completed, False if suspended
        """
        if coro.completed:
            return True
        
        if coro.suspended:
            # Resume suspended coroutine
            coro.suspended = False
        
        self.current = coro
        self.task_counter += 1
        
        try:
            # Execute one step of the coroutine
            result = self.vm._run_coroutine_until_yield(coro)
        except VMError as e:
            # Propagate errors with context
            raise VMError(f"Coroutine '{coro.name}' error: {e}")
        except Exception as e:
            raise VMError(f"Coroutine '{coro.name}' crashed: {e}")
        
        self.current = None
        
        if coro.completed:
            return True
        elif coro.suspended:
            # Check if suspended on a pending operation
            if coro.pending_await is not None:
                # Already in pending queue
                pass
            else:
                # Just suspended, re-queue for later
                self.ready.append(coro)
            return False
        else:
            # Not suspended and not completed - should continue running
            self.ready.append(coro)
            return False
    
    def _handle_pending(self):
        """
        Handle pending coroutines (timers, I/O, etc.).
        
        Checks for:
        - Timed coroutines that should wake up
        - I/O operations that have completed
        """
        if not self.pending:
            return
        
        now = time.time()
        still_pending = []
        
        for task in self.pending:
            if task.wake_time and now >= task.wake_time:
                # Timer expired - ready to run
                task.coroutine.suspended = False
                self.ready.append(task.coroutine)
            elif task.callback and task.callback():
                # I/O completed - ready to run
                task.coroutine.suspended = False
                self.ready.append(task.coroutine)
            else:
                still_pending.append(task)
        
        self.pending = still_pending
        
        # Simple delay if still have pending and nothing ready
        if self.pending and not self.ready:
            next_wake = min(t.wake_time for t in self.pending if t.wake_time)
            delay = max(0, next_wake - time.time())
            if delay > 0:
                time.sleep(min(delay, 0.1))  # Cap at 100ms
    
    def create_task(self, coro: VakCoroutine) -> VakCoroutine:
        """
        Schedule a coroutine for execution.
        
        Args:
            coro: The coroutine to schedule
            
        Returns:
            The same coroutine for chaining
        """
        self.ready.append(coro)
        return coro
    
    def sleep(self, seconds: float) -> VakCoroutine:
        """
        Create a coroutine that sleeps for given seconds.
        
        This is a helper to create timer-based suspension.
        
        Usage:
            लूप = घटना_लूप()
            प्रतीक्षा लूप.निद्रा(१.०)  # await loop.sleep(1.0)
        
        Args:
            seconds: Number of seconds to sleep
            
        Returns:
            A coroutine that will complete after the delay
        """
        # Create a simple coroutine that just waits
        from .bytecode import Bytecode
        from .opcodes import OpCode
        
        # Create minimal bytecode for sleep
        bc = Bytecode(f"<sleep:{seconds}>")
        bc.num_params = 0
        bc.var_names = ['_result']
        bc.code = bytes([
            OpCode.LOAD_CONST, 0, 0,  # Load seconds
            OpCode.CALL_BUILTIN, 0, 1,  # Call sleep builtin (index 0 = 'निद्रा')
            OpCode.RETURN_VOID
        ])
        bc.constants = [seconds]
        bc.functions = {}
        bc.global_names = set()
        
        frame = self.vm._create_frame(bc)
        coro = VakCoroutine(frame, bc)
        
        # Mark as pending with wake time
        wake_time = time.time() + seconds
        self.pending.append(VakPendingTask(coro, wake_time=wake_time))
        coro.suspended = True
        
        return coro
    
    def schedule_timer(self, coro: VakCoroutine, delay: float) -> VakPendingTask:
        """
        Schedule a coroutine to run after a delay.
        
        Args:
            coro: The coroutine to schedule
            delay: Delay in seconds
            
        Returns:
            The pending task
        """
        wake_time = time.time() + delay
        task = VakPendingTask(coro, wake_time=wake_time)
        coro.suspended = True
        self.pending.append(task)
        return task
    
    def schedule_io(self, coro: VakCoroutine, 
                    check_callback: Callable) -> VakPendingTask:
        """
        Schedule a coroutine to run when I/O is ready.
        
        Args:
            coro: The coroutine to schedule
            check_callback: Function that returns True when I/O is ready
            
        Returns:
            The pending task
        """
        task = VakPendingTask(coro, callback=check_callback)
        coro.suspended = True
        self.pending.append(task)
        return task
    
    def stop(self):
        """Stop the event loop immediately."""
        self.stopped = True
    
    def is_running(self) -> bool:
        """Check if the event loop is running."""
        return not self.stopped and (self.ready or self.pending)
    
    def task_count(self) -> int:
        """Get the number of active tasks."""
        return len(self.ready) + len(self.pending)
    
    def status(self) -> dict:
        """Get event loop status."""
        return {
            'running': self.is_running(),
            'ready_count': len(self.ready),
            'pending_count': len(self.pending),
            'current': self.current.name if self.current else None,
            'tasks_run': self.task_counter
        }


# Convenience function to run async code
def चलाओ(main_coro: VakCoroutine) -> Any:
    """
    Run an async coroutine to completion.
    
    This is the main entry point for executing async VakyaLang code.
    
    Usage:
        async def मुख्य():
            प्रतीक्षा कार्य_१()
            प्रतीक्षा कार्य_२()
        
        चलाओ(मुख्य())
    
    Args:
        main_coro: The main coroutine to execute
        
    Returns:
        The result of the coroutine
    """
    loop = VakEventLoop()
    return loop.run(main_coro)


# Alternative name in English
def run_async(main_coro: VakCoroutine) -> Any:
    """English alias for चलाओ."""
    return चलाओ(main_coro)


# Builtin sleep function for use in coroutines
async def निद्रा(seconds: float) -> None:
    """
    Sleep for a given number of seconds.
    
    Usage in VakyaLang:
        प्रतीक्षा निद्रा(१.०)  # await sleep(1.0)
    
    Args:
        seconds: Number of seconds to sleep
    """
    # This is a placeholder - actual implementation requires
    # compiler support to generate the right bytecode
    pass
