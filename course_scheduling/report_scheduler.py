"""
Sleep-loop scheduler for recurring schedule report runs.

Owns only the question of when to run again: it computes the next scheduled
slot, sleeps until then, and invokes a caller-supplied callback in-process. The
loop entry supplies a callback that starts one short-lived report subprocess per
scheduled fire, keeping the long-lived scheduler free of the report pipeline.

Schedule:
  Mon-Thu: 8:03am
  Fri:     8:03am and 6:07pm
  Sat-Sun: skip (sleeps until Monday 8:03am)
"""

# Standard Library
import time
import datetime
import collections.abc

# Schedule: list of (weekday, hour, minute) tuples.
# weekday uses Monday=0 .. Sunday=6 (matching datetime.weekday()).
SCHEDULE = []
# Mon-Fri at 8:03am
for _dow in range(5):
	SCHEDULE.append((_dow, 8, 3))
# Friday at 6:07pm
SCHEDULE.append((4, 18, 7))


#============================================

def next_run_time(now: datetime.datetime) -> datetime.datetime:
	"""
	Calculate the next scheduled run time from now.

	Args:
		now: Current datetime.

	Returns:
		Datetime of the next scheduled slot.
	"""
	# Check remaining slots today
	for dow, hour, minute in SCHEDULE:
		if dow != now.weekday():
			continue
		candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
		if candidate > now:
			return candidate

	# Check each of the next 7 days for the earliest slot
	for days_ahead in range(1, 8):
		future_date = now.date() + datetime.timedelta(days=days_ahead)
		future_dow = future_date.weekday()
		for dow, hour, minute in SCHEDULE:
			if dow == future_dow:
				candidate = datetime.datetime.combine(
					future_date,
					datetime.time(hour, minute),
				)
				return candidate

	# Should never reach here with a weekly schedule
	raise RuntimeError("No scheduled slots found within 7 days")


#============================================

def format_duration(seconds: int) -> str:
	"""
	Format a duration in seconds as a human-readable string.

	Args:
		seconds: Number of seconds.

	Returns:
		String like '2h 15m' or '45m'.
	"""
	hours = seconds // 3600
	mins = (seconds % 3600) // 60
	if hours > 0:
		return f"{hours}h {mins}m"
	return f"{mins}m"


#============================================

def run_loop(callback: collections.abc.Callable[[], None]) -> None:
	"""
	Sleep until the next scheduled slot, then run the callback, forever.

	Args:
		callback: Zero-argument callable run at each scheduled slot. The caller
			binds the report run (term and subjects) into this callback so the
			scheduler stays term- and subject-agnostic.
	"""
	print("=== Course schedule email loop started ===")
	print("  schedule: Mon-Thu 8:03am, Fri 8:03am + 6:07pm")
	print(flush=True)

	while True:
		now = datetime.datetime.now()
		target = next_run_time(now)
		wait_secs = int((target - now).total_seconds())
		target_str = target.strftime("%a %B %-d at %-I:%M%p")
		duration_str = format_duration(wait_secs)
		timestamp = now.strftime("%Y-%m-%d %H:%M")
		print(f"[{timestamp}] Next run: {target_str} (sleeping {duration_str})", flush=True)
		time.sleep(wait_secs)

		# Run the report in-process at the scheduled slot.
		now = datetime.datetime.now()
		timestamp = now.strftime("%Y-%m-%d %H:%M")
		print(f"\n[{timestamp}] Running scheduled report ...", flush=True)
		callback()
		now = datetime.datetime.now()
		timestamp = now.strftime("%Y-%m-%d %H:%M")
		print(f"[{timestamp}] Done\n", flush=True)

		# Small buffer so we don't re-fire the same minute.
		time.sleep(90)
