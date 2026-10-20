"""Quick tests for the PawPal+ logic layer."""

from datetime import date

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task


def test_mark_complete_changes_task_status():
    """A task is due until mark_complete() is called for that day."""
    today = date.today()
    task = Task("Morning walk", 30, priority="high")

    assert task.is_due_today(today) is True
    assert task.is_complete(today) is False

    task.mark_complete(today)

    assert task.last_completed == today
    assert task.is_complete(today) is True
    assert task.is_due_today(today) is False


def test_adding_task_increases_pet_task_count():
    """add_task() appends to the pet's task list."""
    pet = Pet(name="Biscuit", species="dog", breed="Golden Retriever")

    assert len(pet.get_tasks()) == 0

    pet.add_task(Task("Breakfast", 10, priority="high"))
    assert len(pet.get_tasks()) == 1

    pet.add_task(Task("Evening walk", 25, priority="medium"))
    assert len(pet.get_tasks()) == 2


def make_scheduler() -> Scheduler:
    """Build a scheduler for two pets whose tasks were added out of time order."""
    owner = Owner(name="Marcos", available_minutes=120)
    dog = Pet(name="Biscuit", species="dog")
    dog.add_task(Task("Evening walk", 25, preferred_time="18:00"))
    dog.add_task(Task("Brush", 10))
    dog.add_task(Task("Breakfast", 10, preferred_time="08:00"))
    cat = Pet(name="Luna", species="cat")
    cat.add_task(Task("Play", 20, preferred_time="afternoon"))
    owner.add_pet(dog)
    owner.add_pet(cat)
    return Scheduler(owner)


def test_sort_by_time_orders_by_preferred_time_with_unset_last():
    """sort_by_time() handles HH:MM and named times, and puts unset times last."""
    scheduler = make_scheduler()
    ordered = scheduler.sort_by_time(scheduler.owner.get_all_tasks())

    assert [task.title for _, task in ordered] == [
        "Breakfast", "Play", "Evening walk", "Brush",
    ]


def test_filter_by_pet_name_and_completion_status():
    """filter_by() narrows by pet, by status, or by both together."""
    scheduler = make_scheduler()
    today = date.today()
    tasks = scheduler.owner.get_all_tasks()
    scheduler.owner.pets[0].tasks[2].mark_complete(today)  # Breakfast

    luna = scheduler.filter_by(tasks, today, pet_name="Luna")
    done = scheduler.filter_by(tasks, today, completed=True)
    biscuit_pending = scheduler.filter_by(tasks, today, pet_name="Biscuit", completed=False)

    assert [task.title for _, task in luna] == ["Play"]
    assert [task.title for _, task in done] == ["Breakfast"]
    assert [task.title for _, task in biscuit_pending] == ["Evening walk", "Brush"]


def test_completing_daily_task_creates_next_occurrence_tomorrow():
    """mark_task_complete() on a daily task adds a copy due today + 1 day."""
    scheduler = make_scheduler()
    today = date(2026, 10, 20)

    next_task = scheduler.mark_task_complete("Biscuit", "Breakfast", today)
    breakfasts = [t for t in scheduler.owner.pets[0].tasks if t.title == "Breakfast"]

    assert len(breakfasts) == 2
    assert breakfasts[0].completed is True
    assert next_task in breakfasts
    assert next_task.completed is False
    assert next_task.due_date == date(2026, 10, 21)
    assert next_task.is_due_today(today) is False
    assert next_task.is_due_today(date(2026, 10, 21)) is True


def test_completing_weekly_task_creates_next_occurrence_in_seven_days():
    """A weekly task's next occurrence is due a week later, across month ends."""
    pet = Pet(name="Luna", species="cat")
    pet.add_task(Task("Nail trim", 15, frequency="weekly"))

    next_task = pet.complete_task("Nail trim", date(2026, 10, 28))

    assert next_task.due_date == date(2026, 11, 4)
    assert pet._find_task("Nail trim") is next_task  # pending instance wins


def test_detect_time_conflicts_warns_for_same_and_different_pets():
    """Overlapping preferred times produce warnings, labelled by pet."""
    dog = Pet(name="Biscuit", species="dog")
    cat = Pet(name="Luna", species="cat")
    dog.add_task(Task("Breakfast", 10, preferred_time="08:00"))
    dog.add_task(Task("Meds", 5, preferred_time="08:05"))
    cat.add_task(Task("Breakfast", 10, preferred_time="08:00"))
    owner = Owner(name="Marcos", available_minutes=60)
    owner.add_pet(dog)
    owner.add_pet(cat)

    warnings = Scheduler(owner).detect_time_conflicts(owner.get_all_tasks())

    assert len(warnings) == 3
    assert any("same pet (Biscuit)" in w and "Meds" in w for w in warnings)
    assert sum("different pets" in w for w in warnings) == 2


def test_detect_time_conflicts_ignores_back_to_back_and_unset_times():
    """Tasks that only touch, or have no preferred time, are not conflicts."""
    pet = Pet(name="Biscuit", species="dog")
    pet.add_task(Task("Morning walk", 30, preferred_time="07:30"))
    pet.add_task(Task("Breakfast", 10, preferred_time="08:00"))
    pet.add_task(Task("Brush", 10))
    owner = Owner(name="Marcos", available_minutes=60)
    owner.add_pet(pet)

    assert Scheduler(owner).detect_time_conflicts(owner.get_all_tasks()) == []


# --- Sorting correctness ---------------------------------------------------

def test_sort_by_time_is_chronological_and_keeps_ties_in_added_order():
    """Times sort earliest first; tasks at the same time keep the order they were added."""
    pet = Pet(name="Biscuit", species="dog")
    pairs = [
        (pet, Task("Dinner", 10, preferred_time="17:30")),
        (pet, Task("Midnight snack", 5, preferred_time="00:00")),
        (pet, Task("Meds", 5, preferred_time="08:00")),
        (pet, Task("Breakfast", 10, preferred_time="08:00")),
        (pet, Task("Lunch", 10, preferred_time="12:15")),
    ]
    owner = Owner(name="Marcos", available_minutes=60)

    ordered = Scheduler(owner).sort_by_time(pairs)

    assert [task.title for _, task in ordered] == [
        "Midnight snack", "Meds", "Breakfast", "Lunch", "Dinner",
    ]


def test_generate_plan_entries_are_in_chronological_order():
    """The plan lists entries by start time, even though high priority tasks are placed first."""
    pet = Pet(name="Biscuit", species="dog")
    pet.add_task(Task("Evening walk", 25, priority="high", preferred_time="18:00"))
    pet.add_task(Task("Play", 15, priority="low", preferred_time="10:00"))
    pet.add_task(Task("Breakfast", 10, priority="medium", preferred_time="08:00"))
    owner = Owner(name="Marcos", available_minutes=120)
    owner.add_pet(pet)

    plan = Scheduler(owner).generate_plan(date(2026, 10, 20))

    assert [e.start_time for e in plan.entries] == ["08:00", "10:00", "18:00"]


# --- Recurrence logic ------------------------------------------------------

def test_completed_daily_task_leaves_today_and_returns_tomorrow():
    """After completion the task drops out of today's plan and is back in tomorrow's."""
    today, tomorrow = date(2026, 10, 20), date(2026, 10, 21)
    pet = Pet(name="Biscuit", species="dog")
    pet.add_task(Task("Walk", 30))
    owner = Owner(name="Marcos", available_minutes=60)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    scheduler.mark_task_complete("Biscuit", "Walk", today)

    assert scheduler.generate_plan(today).entries == []
    tomorrow_plan = scheduler.generate_plan(tomorrow)
    assert [e.task.title for e in tomorrow_plan.entries] == ["Walk"]
    assert tomorrow_plan.entries[0].task.completed is False


def test_weekly_task_is_not_due_until_seven_days_later():
    """A weekly task completed today is not due on day 6 but is due on day 7."""
    pet = Pet(name="Luna", species="cat")
    pet.add_task(Task("Nail trim", 15, frequency="weekly"))

    next_task = pet.complete_task("Nail trim", date(2026, 10, 20))

    assert next_task.is_due_today(date(2026, 10, 26)) is False
    assert next_task.is_due_today(date(2026, 10, 27)) is True


def test_mark_task_complete_unknown_pet_raises():
    """Completing a task for a pet the owner doesn't have raises ValueError."""
    scheduler = Scheduler(Owner(name="Marcos", available_minutes=60))

    with pytest.raises(ValueError):
        scheduler.mark_task_complete("Ghost", "Walk", date(2026, 10, 20))


# --- Conflict detection ----------------------------------------------------

def test_detect_time_conflicts_flags_exact_duplicate_times():
    """Two tasks at exactly the same time produce exactly one warning."""
    pet = Pet(name="Biscuit", species="dog")
    pet.add_task(Task("Breakfast", 10, preferred_time="08:00"))
    pet.add_task(Task("Meds", 10, preferred_time="08:00"))
    owner = Owner(name="Marcos", available_minutes=60)
    owner.add_pet(pet)

    warnings = Scheduler(owner).detect_time_conflicts(owner.get_all_tasks())

    assert len(warnings) == 1
    assert "Breakfast" in warnings[0] and "Meds" in warnings[0]


def test_detect_time_conflicts_matches_named_time_with_clock_time():
    """"morning" means 08:00, so it clashes with a task at 08:00."""
    dog = Pet(name="Biscuit", species="dog")
    cat = Pet(name="Luna", species="cat")
    dog.add_task(Task("Walk", 30, preferred_time="morning"))
    cat.add_task(Task("Breakfast", 10, preferred_time="08:00"))
    owner = Owner(name="Marcos", available_minutes=60)
    owner.add_pet(dog)
    owner.add_pet(cat)

    warnings = Scheduler(owner).detect_time_conflicts(owner.get_all_tasks())

    assert len(warnings) == 1
    assert "different pets" in warnings[0]


def test_generated_plan_has_no_overlaps_even_when_requests_clash():
    """The scheduler moves clashing tasks, so detect_conflicts() on the plan is empty."""
    pet = Pet(name="Biscuit", species="dog")
    pet.add_task(Task("Breakfast", 10, preferred_time="08:00"))
    pet.add_task(Task("Meds", 10, preferred_time="08:00"))
    owner = Owner(name="Marcos", available_minutes=60)
    owner.add_pet(pet)
    scheduler = Scheduler(owner)

    plan = scheduler.generate_plan(date(2026, 10, 20))

    assert len(plan.entries) == 2
    assert scheduler.detect_conflicts(plan) == []


# --- Edge cases ------------------------------------------------------------

def test_owner_with_no_pets_or_pet_with_no_tasks_gives_empty_plan():
    """No tasks means an empty plan, nothing skipped, and no conflicts."""
    owner = Owner(name="Marcos", available_minutes=60)
    scheduler = Scheduler(owner)
    assert scheduler.generate_plan(date(2026, 10, 20)).entries == []

    owner.add_pet(Pet(name="Luna", species="cat"))
    plan = scheduler.generate_plan(date(2026, 10, 20))

    assert plan.entries == [] and plan.skipped == []
    assert scheduler.detect_time_conflicts(owner.get_all_tasks()) == []
    assert scheduler.filter_by(owner.get_all_tasks(), date(2026, 10, 20), pet_name="Luna") == []


def test_zero_available_minutes_skips_every_task():
    """With no time available, every task is skipped with a reason."""
    pet = Pet(name="Biscuit", species="dog")
    pet.add_task(Task("Walk", 30))
    pet.add_task(Task("Breakfast", 10))
    owner = Owner(name="Marcos", available_minutes=0)
    owner.add_pet(pet)

    plan = Scheduler(owner).generate_plan(date(2026, 10, 20))

    assert plan.entries == []
    assert len(plan.skipped) == 2
    assert all("only 0 min left" in e.reason for e in plan.skipped)


def test_task_that_would_run_past_midnight_is_skipped():
    """A task starting at 23:50 that lasts 20 minutes doesn't fit in the day."""
    pet = Pet(name="Luna", species="cat")
    pet.add_task(Task("Late play", 20, preferred_time="23:50"))
    owner = Owner(name="Marcos", available_minutes=60)
    owner.add_pet(pet)

    plan = Scheduler(owner).generate_plan(date(2026, 10, 20))

    assert plan.entries == []
    assert plan.skipped[0].reason == "no free time slot left today"


def test_preferred_time_before_day_start_is_moved_to_day_start():
    """A 07:30 walk is placed at 08:00 when the owner's day starts at 08:00."""
    pet = Pet(name="Biscuit", species="dog")
    pet.add_task(Task("Walk", 30, preferred_time="07:30"))
    owner = Owner(name="Marcos", available_minutes=60, day_start="08:00")
    owner.add_pet(pet)

    plan = Scheduler(owner).generate_plan(date(2026, 10, 20))

    assert plan.entries[0].start_time == "08:00"
    assert "day starts at 08:00" in plan.entries[0].reason


@pytest.mark.parametrize("bad_time", ["25:00", "8am", "noon", "12:60"])
def test_invalid_preferred_time_raises(bad_time):
    """Times that aren't valid HH:MM or a known part of the day are rejected."""
    with pytest.raises(ValueError):
        Task("Walk", 30, preferred_time=bad_time)
