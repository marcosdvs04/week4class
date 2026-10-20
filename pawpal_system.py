"""PawPal+ logic layer: backend classes for owners, pets, tasks, and scheduling."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

PRIORITY_VALUES = {"low": 1, "medium": 2, "high": 3}
FREQUENCIES = ("daily", "weekly")
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

    def __post_init__(self) -> None:
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")
        if self.priority not in PRIORITY_VALUES:
            raise ValueError(f"priority must be one of {list(PRIORITY_VALUES)}")
        if self.frequency not in FREQUENCIES:
            raise ValueError(f"frequency must be one of {list(FREQUENCIES)}")

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
        """Return True if this task should be scheduled on the given day."""
        if self.last_completed is None:
            return True
        days_since = (day - self.last_completed).days
        if self.frequency == "weekly":
            return days_since >= 7
        return days_since >= 1

    def is_complete(self, day: date) -> bool:
        """Return True if this task was already done for the given day."""
        return not self.is_due_today(day)

    def mark_complete(self, day: date) -> None:
        """Record that this task was done on the given day."""
        self.last_completed = day


@dataclass
class Pet:
    """A pet and the care tasks it needs."""

    name: str
    species: str  # "dog" | "cat" | "other"
    breed: str = ""
    tasks: list[Task] = field(default_factory=list)

    def _find_task(self, title: str) -> Task:
        for task in self.tasks:
            if task.title == title:
                return task
        raise ValueError(f"{self.name} has no task named {title!r}")

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet."""
        if any(t.title == task.title for t in self.tasks):
            raise ValueError(f"{self.name} already has a task named {task.title!r}")
        self.tasks.append(task)

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
        self.owner = owner

    def generate_plan(self, day: date) -> DailyPlan:
        """Build the plan for the given day.

        Due tasks are placed back-to-back from the owner's day_start in sorted
        order. A task that doesn't fit in the remaining time is skipped, and
        shorter tasks after it can still be placed.
        """
        plan = DailyPlan(day)
        current = to_minutes(self.owner.day_start)
        remaining = self.owner.available_minutes

        for pet, task in self.sort_tasks(self.filter_tasks(self.owner.get_all_tasks(), day)):
            if task.duration_minutes > remaining:
                plan.skip(
                    task, pet,
                    f"needs {task.duration_minutes} min but only {remaining} min left",
                )
                continue
            plan.add_entry(task, pet, to_hhmm(current), self._reason(task))
            current += task.duration_minutes
            remaining -= task.duration_minutes

        return plan

    def sort_tasks(self, tasks: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """Order (pet, task) pairs by priority, then by preferred time or duration.

        Higher priority comes first. Within a priority, tasks with an earlier
        preferred time come first, tasks with no preference go last, and
        shorter tasks break any remaining ties.
        """
        def key(pair: tuple[Pet, Task]) -> tuple:
            task = pair[1]
            preferred = task.preferred_minutes()
            return (
                -task.priority_value(),
                preferred is None,
                preferred or 0,
                task.duration_minutes,
            )

        return sorted(tasks, key=key)

    def filter_tasks(self, tasks: list[tuple[Pet, Task]], day: date) -> list[tuple[Pet, Task]]:
        """Keep only (pet, task) pairs whose task is due on the given day."""
        return [(pet, task) for pet, task in tasks if task.is_due_today(day)]

    def detect_conflicts(self, plan: DailyPlan) -> list[str]:
        """Return warnings for any overlapping scheduled tasks."""
        warnings = []
        entries = sorted(plan.entries, key=lambda e: to_minutes(e.start_time))
        for i, earlier in enumerate(entries):
            for later in entries[i + 1:]:
                if to_minutes(later.start_time) >= to_minutes(earlier.end_time):
                    break
                warnings.append(
                    f"{earlier.task.title} ({earlier.pet.name}, {earlier.start_time}-"
                    f"{earlier.end_time}) overlaps {later.task.title} "
                    f"({later.pet.name}, {later.start_time}-{later.end_time})"
                )
        return warnings

    def _reason(self, task: Task) -> str:
        reason = f"{task.priority} priority"
        if task.preferred_time:
            reason += f", preferred {task.preferred_time}"
        return reason
