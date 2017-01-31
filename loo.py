################################################################################
"""
	LOOPY loo.py

loopy subclasses the local system's default asyncio loop class and permits
one to issue exceptions from other threads that will be contained within the
currently running task and the loop will continue executing other tasks even
if unhandled.

The class includes a diagnosis tool that spawns a separate thread to keep track
of performance. If the loop does not complete a cycle in 3 seconds, it will
interrupt the currently running task and continue to the next in order to ensure
flow. A stacktrace will be printed.

ISSUES: There is the possibility that the loop will switch tasks after spending
3 seconds but before the interrupt is handled, causing the next task to catch
the exception instead.
"""
################################################################################

from asyncio   import DefaultEventLoopPolicy
from ctypes    import pythonapi, py_object
from inspect   import isclass
from sys       import stderr
from threading import Timer
from traceback import print_exc
from time      import sleep

class InterruptableEventLoop(DefaultEventLoopPolicy._loop_factory):
	"""An Event loop whith an accompanying diagnostic thread where individial
	tasks can be interrupted from other threads and the loop will continue."""

	def __init__(self):
		"""Initialize loop cycle counter"""
		super().__init__()
		self.cycle = 0

	def raise_exc(self, exctype=TaskInterrupt):
		"""Raises the given Exception type in the context of the loop thread regardless
		of which thread calls the method."""
		if not isclass(exctype):
			raise TypeError("Only types can be raised (not instances)")
		tid = self._thread_id
		if tid is None:
			raise RuntimeError("Event loop is not running.")
		# raise the exception and perform cleanup if needed
		res = pythonapi.PyThreadState_SetAsyncExc(tid, py_object(exctype))
		if res is not 1:
			if res == 0:
				raise ValueError("Invalid thread id.") # did the thread stop right before raising?
			else:
				# if it returns a number greater than one, you're in trouble, 
				# and you should call it again with exc=NULL to roll back the effect
				pythonapi.PyThreadState_SetAsyncExc(tid, None)
				raise SystemError("PyThreadState_SetAsyncExc failed")

	def create_task(self, coro):
		"""Wrap the new task in a try-catch for stopping interrupts
		from affecting more than one task."""
		async def wrapper():
			try:
				return await coro
			except TaskInterrupt:
				# The task has been interrupted. Print a stacktrace and exit the task.
				print_exc()
		return super().create_task(wrapper())

	def _run_once(self):
		"""Perform one loop cycle then increment a counter"""
		super()._run_once()
		self.cycle += 1

	def run_forever(self):
		"""The start of a loop's execution.
		Spawn a new thread to track loop performance before start."""
		timeoutcount = 0
		
		def diagnose():
			"""Will run in its own thread and check up on the loop routinely"""
			nonlocal timeoutcount
			while self.is_running():
				if self.cycle <= 10: # Less than 10 iterations per second
					if self.cycle is 0:
						timeoutcount += 1 # Loop has completely halted. Do a countdown
					else:
						timeoutcount = 0
					if timeoutcount >= 3: # Loop has not had progress in 3 seconds
						print('[ERROR] Event loop is not progressing.', file=stderr)
						# Interrupt the loop (hopefully still in the stuck task)
						self.raise_exc()
					else:
						print('[WARNING] Event loop is very slow.', file=stderr)
				self.cycle = 0
				sleep(1) # set diagnostics thread on hold

		Timer(1, diagnose).start()
		super().run_forever()

class TaskInterrupt(Exception):
	"""Custom Exception type to avoid conflicts"""
	pass

# test/demonstration of function
if __name__ is '__main__':

	from asyncio import set_event_loop

	async def slowcoro():
		"""Test case of a misbehaving coroutine"""
		while True:
			# the following number is low because python can't handle exceptions
			# while the thread is sleeping. Never use time.sleep in async code!
			# use asyncio.sleep instead.
			sleep(0.1) # get through this
		print("I will never run")

	loop = InterruptableEventLoop()
	set_event_loop(loop)
	loop.run_until_complete(slowcoro())