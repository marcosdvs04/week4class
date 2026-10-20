"""PawPal+ logic layer: backend classes for owners, pets, tasks, and scheduling.

Skeleton generated from diagrams/uml.mmd. Method bodies are stubs to be
implemented in later phases.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class Task:
    """A single pet care activity, such as a walk, feeding, or medication."""

    title: str
    duration_minutes: int
    priority: str = "medium"  # "low" | "medium" | "high"
    category: str = "general"  # walk, feeding, meds, enrichment, grooming, ...
    preferred_time: Optional[str] = None  # e.g. "morning" or "08:00"
    frequency: str = "daily"  # "daily" | "weekly"
    completed: bool = False

    def priority_value(self) -> int:
        """Return a numeric rank for sorting (high=3, medium=2, low=1)."""
        pass

    def is_due_today(self, day: date) -> bool:
        """Return True if this task should be scheduled on the given day."""
        pass

    def mark_complete(self) -> None:
        """Mark this task as done."""
        pass


@dataclass
class Pet:
    """A pet and the care tasks it needs."""

    name: str
    species: str  # "dog" | "cat" | "other"
    breed: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet."""
        pass

    def remove_task(self, title: str) -> None:
        """Remove the task with the given title."""
        pass

    def edit_task(self, title: str, changes: dict) -> None:
        """Update fields on the task with the given title."""
        pass

    def get_tasks(self) -> list[Task]:
        """Return all tasks for this pet."""
        pass


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
        pass

    def get_pets(self) -> list[Pet]:
        """Return all of this owner's pets."""
        pass

    def update_availability(self, minutes: int) -> None:
        """Change how many minutes the owner has for pet care today."""
        pass


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
        pass

    def skip(self, task: Task, pet: Pet, reason: str) -> None:
        """Record a task that was left out of the plan and why."""
        pass

    def total_minutes(self) -> int:
        """Return the total scheduled minutes."""
        pass

    def summary(self) -> str:
        """Return a readable version of the plan for display."""
        pass


class Scheduler:
    """Builds a DailyPlan from an owner's pets, tasks, and constraints."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def generate_plan(self, day: date) -> DailyPlan:
        """Build the plan for the given day."""
        pass

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Order tasks by priority, then by preferred time or duration."""
        pass

    def filter_tasks(self, tasks: list[Task], day: date) -> list[Task]:
        """Keep only tasks that are due on the given day and not completed."""
        pass

    def detect_conflicts(self, plan: DailyPlan) -> list[str]:
        """Return warnings for any overlapping scheduled tasks."""
        pass
