"""PawPal+ logic layer: backend classes for owners, pets, tasks, and scheduling."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from typing import Optional

PRIORITY_VALUES = {"low": 1, "medium": 2, "high": 3}
FREQUENCIES = ("daily", "weekly")
# Days until the next occurrence of a recurring task.
RECURRENCE_DAYS = {"daily": 1, "weekly": 7}
# Rough start of each named part of the day, in minutes after midnight.
TIME_OF_DAY = {"morning": 8 * 60, "afternoon": 12 * 60, "evening": 17 * 60}


def to_minutes(hhmm: str) -> int:
    """Convert "HH:MM" to minutes after midnight."""
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)


def to_hhmm(minutes: int) -> str:
    """Convert minutes after midnight to "HH:MM"."""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


@dataclass
class Task:
    """A single pet care activity, such as a walk, feeding, or medication."""

    title: str
    duration_minutes: int
    priority: str = "medium"  # "low" | "medium" | "high"
    category: str = "general"  # walk, feeding, meds, enrichment, grooming, ...
    preferred_time: Optional[str] = None  # e.g. "morning" or "08:00"
    frequency: str = "daily"  # "daily" | "weekly"
    last_completed: Optional[date] = None
    due_date: Optional[date] = None  # None means due now
    completed: bool = False

    def __post_init__(self) -> None:
        """Reject invalid duration, priority, or frequency values."""
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")
        if self.priority not in PRIORITY_VALUES:
            raise ValueError(f"priority must be one of {list(PRIORITY_VALUES)}")
        if self.frequency not in FREQUENCIES:
            raise ValueError(f"frequency must be one of {list(FREQUENCIES)}")
        if self.preferred_time is not None and self.preferred_time not in TIME_OF_DAY:
            try:
                minutes = to_minutes(self.preferred_time)
            except ValueError:
                minutes = -1
            if not 0 <= minutes < 24 * 60:
                raise ValueError(
                    "preferred_time must be HH:MM or one of morning/afternoon/evening"
                )

    def priority_value(self) -> int:
        """Return a numeric rank for sorting (high=3, medium=2, low=1)."""
        return PRIORITY_VALUES[self.priority]

    def preferred_minutes(self) -> Optional[int]:
        """Return the preferred time as minutes after midnight, or None if unset."""
        if self.preferred_time is None:
            return None
        if self.preferred_time in TIME_OF_DAY:
            return TIME_OF_DAY[self.preferred_time]
        return to_minutes(self.preferred_time)

    def is_due_today(self, day: date) -> bool:
        """Return True if this task is not done and its due date has arrived.

        A task with no due_date is due right away. A next occurrence created
        by mark_complete() stays hidden until its due_date.
        """
        if self.completed:
            return False
        return self.due_date is None or self.due_date <= day

    def is_complete(self, day: date) -> bool:
        """Return True if this task instance has been marked done.

        Each occurrence of a recurring task is its own Task, so this is just
        the completed flag. The day argument is kept so callers can treat it
        like is_due_today().
        """
        return self.completed

    def next_due_date(self, day: date) -> date:
        """Return the due date of the next occurrence after completing on day.

        Adds a timedelta of 1 day (daily) or 7 days (weekly), so month and
        year boundaries are handled by the date type.
        """
        return day + timedelta(days=RECURRENCE_DAYS[self.frequency])

    def mark_complete(self, day: date) -> Task:
        """Mark this task done on the given day and return its next occurrence.

        The returned task is a fresh, not-completed copy due one day later for
        daily tasks or seven days later for weekly tasks. The caller decides
        whether to add it to a pet (see Pet.complete_task).
        """
        self.completed = True
        self.last_completed = day
        return replace(self, due_date=self.next_due_date(day), completed=False)


@dataclass
class Pet:
    """A pet and the care tasks it needs."""

    name: str
    species: str  # "dog" | "cat" | "other"
    breed: str = ""
    tasks: list[Task] = field(default_factory=list)

    def _find_task(self, title: str) -> Task:
        """Return the task with the given title, or raise ValueError if missing.

        A recurring task can have a completed instance and a pending one with
        the same title; the pending one is returned when there is one.
        """
        matches = [task for task in self.tasks if task.title == title]
        if not matches:
            raise ValueError(f"{self.name} has no task named {title!r}")
        pending = [task for task in matches if not task.completed]
        return pending[0] if pending else matches[0]

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet.

        Raises ValueError if a pending task with the same title exists.
        Completed tasks with that title are fine, since they are history.
        """
        if any(t.title == task.title and not t.completed for t in self.tasks):
            raise ValueError(f"{self.name} already has a task named {task.title!r}")
        self.tasks.append(task)

    def complete_task(self, title: str, day: date) -> Task:
        """Mark the pending task with this title done and add its next occurrence.

        The completed task stays in the list as history, and the new
        occurrence is appended and returned. Raises ValueError if there is
        no pending task with that title.
        """
        task = self._find_task(title)
        if task.completed:
            raise ValueError(f"{self.name}'s {title!r} is already completed")
        next_task = task.mark_complete(day)
        self.tasks.append(next_task)
        return next_task

    def remove_task(self, title: str) -> None:
        """Remove the task with the given title."""
        self.tasks.remove(self._find_task(title))

    def edit_task(self, title: str, changes: dict) -> None:
        """Update fields on the task with the given title."""
        task = self._find_task(title)
        for name in changes:
            if not hasattr(task, name):
                raise ValueError(f"Task has no field {name!r}")
        updated = Task(**{**task.__dict__, **changes})  # re-runs validation
        self.tasks[self.tasks.index(task)] = updated

    def get_tasks(self) -> list[Task]:
        """Return all tasks for this pet."""
        return list(self.tasks)


@dataclass
class Owner:
    """The pet owner, who supplies the day's time limit and preferences."""

    name: str
    available_minutes: int
    day_start: str = "08:00"
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Attach a pet to this owner."""
        if any(p.name == pet.name for p in self.pets):
            raise ValueError(f"{self.name} already has a pet named {pet.name!r}")
        self.pets.append(pet)

    def get_pets(self) -> list[Pet]:
        """Return all of this owner's pets."""
        return list(self.pets)

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every task across all pets, paired with the pet it belongs to."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]

    def update_availability(self, minutes: int) -> None:
        """Change how many minutes the owner has for pet care today."""
        if minutes < 0:
            raise ValueError("available minutes cannot be negative")
        self.available_minutes = minutes


@dataclass
class ScheduledTask:
    """One entry in a daily plan: a task placed at a time, with the reason why."""

    task: Task
    pet: Pet
    start_time: Optional[str] = None  # None for skipped tasks
    end_time: Optional[str] = None
    reason: str = ""


@dataclass
class DailyPlan:
    """The generated schedule for one day, including tasks that were skipped."""

    day: date
    entries: list[ScheduledTask] = field(default_factory=list)
    skipped: list[ScheduledTask] = field(default_factory=list)

    def add_entry(self, task: Task, pet: Pet, start_time: str, reason: str) -> None:
        """Schedule a task at the given start time and record why."""
        end_time = to_hhmm(to_minutes(start_time) + task.duration_minutes)
        self.entries.append(ScheduledTask(task, pet, start_time, end_time, reason))

    def skip(self, task: Task, pet: Pet, reason: str) -> None:
        """Record a task that was left out of the plan and why."""
        self.skipped.append(ScheduledTask(task, pet, reason=reason))

    def total_minutes(self) -> int:
        """Return the total scheduled minutes."""
        return sum(entry.task.duration_minutes for entry in self.entries)

    def summary(self) -> str:
        """Return a readable version of the plan for display."""
        lines = [f"Daily plan for {self.day.isoformat()} ({self.total_minutes()} min):"]
        if not self.entries:
            lines.append("  Nothing scheduled.")
        for e in self.entries:
            lines.append(
                f"  {e.start_time}-{e.end_time}  {e.task.title} ({e.pet.name}) "
                f"[priority: {e.task.priority}] - {e.reason}"
            )
        if self.skipped:
            lines.append("Skipped:")
            for e in self.skipped:
                lines.append(f"  {e.task.title} ({e.pet.name}) - {e.reason}")
        return "\n".join(lines)


class Scheduler:
    """Builds a DailyPlan from an owner's pets, tasks, and constraints."""

    def __init__(self, owner: Owner) -> None:
        """Create a scheduler that plans around this owner's pets and constraints."""
        self.owner = owner

    def generate_plan(self, day: date) -> DailyPlan:
        """Build the plan for the given day.

        Due tasks are placed in sorted order, so higher priority tasks claim
        their slots first. A task with a preferred time starts at that time if
        it is free, otherwise at the next free slot after it; a task with no
        preference takes the earliest free slot from the owner's day_start.
        A task is skipped if it would go over the owner's available minutes
        or no slot is left before midnight. Entries end up in time order.
        """
        plan = DailyPlan(day)
        day_start = to_minutes(self.owner.day_start)
        remaining = self.owner.available_minutes

        for pet, task in self.sort_tasks(self.filter_tasks(self.owner.get_all_tasks(), day)):
            if task.duration_minutes > remaining:
                plan.skip(
                    task, pet,
                    f"needs {task.duration_minutes} min but only {remaining} min left",
                )
                continue
            preferred = task.preferred_minutes()
            desired = day_start if preferred is None else max(preferred, day_start)
            start = self._find_slot(plan, desired, task.duration_minutes)
            if start is None:
                plan.skip(task, pet, "no free time slot left today")
                continue
            plan.add_entry(task, pet, to_hhmm(start), self._reason(task, start, day_start))
            remaining -= task.duration_minutes

        plan.entries.sort(key=lambda e: to_minutes(e.start_time))
        return plan

    def _find_slot(self, plan: DailyPlan, desired: int, duration: int) -> Optional[int]:
        """Return the first start time at or after desired that overlaps nothing."""
        start = desired
        for entry in sorted(plan.entries, key=lambda e: to_minutes(e.start_time)):
            entry_start, entry_end = to_minutes(entry.start_time), to_minutes(entry.end_time)
            if start + duration <= entry_start:
                break
            if start < entry_end:
                start = entry_end
        return start if start + duration <= 24 * 60 else None

    def mark_task_complete(self, pet_name: str, title: str, day: date) -> Task:
        """Complete a pet's task on the given day and return its next occurrence.

        Looks up the pet by name and delegates to Pet.complete_task().
        Raises ValueError if the owner has no pet with that name.
        """
        for pet in self.owner.pets:
            if pet.name == pet_name:
                return pet.complete_task(title, day)
        raise ValueError(f"{self.owner.name} has no pet named {pet_name!r}")

    def sort_tasks(self, tasks: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """Order (pet, task) pairs by priority, then by preferred time or duration.

        Higher priority comes first. Within a priority, tasks with an earlier
        preferred time come first, tasks with no preference go last, and
        shorter tasks break any remaining ties.
        """
        def key(pair: tuple[Pet, Task]) -> tuple:
            """Build the sort key: priority, has preference, preferred time, duration."""
            task = pair[1]
            preferred = task.preferred_minutes()
            return (
                -task.priority_value(),
                preferred is None,
                preferred or 0,
                task.duration_minutes,
            )

        return sorted(tasks, key=key)

    def sort_by_time(self, tasks: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """Order (pet, task) pairs by preferred time, earliest first.

        Names like "morning" are converted to minutes so they sort alongside
        "HH:MM" times. Tasks with no preferred time go last.
        """
        return sorted(
            tasks,
            key=lambda pair: (
                pair[1].preferred_minutes() is None,
                pair[1].preferred_minutes() or 0,
            ),
        )

    def filter_tasks(self, tasks: list[tuple[Pet, Task]], day: date) -> list[tuple[Pet, Task]]:
        """Keep only (pet, task) pairs whose task is due on the given day."""
        return [(pet, task) for pet, task in tasks if task.is_due_today(day)]

    def filter_by(
        self,
        tasks: list[tuple[Pet, Task]],
        day: date,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> list[tuple[Pet, Task]]:
        """Keep (pet, task) pairs matching a pet name and/or completion status.

        Leave a filter as None to ignore it; set both to combine them, e.g.
        pet_name="Luna", completed=False for Luna's pending tasks. The day is
        passed to Task.is_complete().
        """
        return [
            (pet, task)
            for pet, task in tasks
            if (pet_name is None or pet.name == pet_name)
            and (completed is None or task.is_complete(day) == completed)
        ]

    def detect_conflicts(self, plan: DailyPlan) -> list[str]:
        """Return warnings for any overlapping scheduled tasks in a finished plan.

        generate_plan() never places tasks on top of each other, so this is a
        safety check and should normally return an empty list. To warn about
        clashing requested times, use detect_time_conflicts().
        """
        windows = [
            (e.pet, e.task, to_minutes(e.start_time), to_minutes(e.end_time))
            for e in plan.entries
        ]
        return self._overlap_warnings(windows)

    def detect_time_conflicts(self, tasks: list[tuple[Pet, Task]]) -> list[str]:
        """Return warnings for tasks whose preferred times overlap.

        Each task with a preferred time asks for the window [preferred,
        preferred + duration). Two windows that overlap are a conflict, for
        the same pet or for different pets. Tasks with no preferred time are
        ignored. This only warns; it never raises or changes any task.
        """
        windows = [
            (pet, task, task.preferred_minutes(),
             task.preferred_minutes() + task.duration_minutes)
            for pet, task in tasks
            if task.preferred_minutes() is not None
        ]
        return self._overlap_warnings(windows)

    def _overlap_warnings(self, windows: list[tuple[Pet, Task, int, int]]) -> list[str]:
        """Return a warning for each overlapping pair of (pet, task, start, end) windows.

        Windows are sorted by start, so each one only needs comparing with
        the ones after it that start before it ends.
        """
        warnings = []
        windows = sorted(windows, key=lambda w: w[2])
        for i, (pet_a, task_a, start_a, end_a) in enumerate(windows):
            for pet_b, task_b, start_b, end_b in windows[i + 1:]:
                if start_b >= end_a:
                    break
                who = f"same pet ({pet_a.name})" if pet_a is pet_b else "different pets"
                warnings.append(
                    f"Conflict, {who}: {task_a.title} ({pet_a.name}, "
                    f"{to_hhmm(start_a)}-{to_hhmm(end_a)}) overlaps {task_b.title} "
                    f"({pet_b.name}, {to_hhmm(start_b)}-{to_hhmm(end_b)})"
                )
        return warnings

    def _reason(self, task: Task, start: int, day_start: int) -> str:
        """Explain why a task was placed at its start time."""
        reason = f"{task.priority} priority"
        preferred = task.preferred_minutes()
        if preferred is None:
            return reason + ", no preferred time, so placed in the earliest free slot"
        if start == preferred:
            return reason + f", at its preferred time ({task.preferred_time})"
        if preferred < day_start and start == day_start:
            return reason + f", prefers {task.preferred_time} but the day starts at {to_hhmm(day_start)}"
        return reason + f", prefers {task.preferred_time} but that slot was taken"
