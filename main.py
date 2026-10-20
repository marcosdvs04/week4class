"""PawPal+ demo script: builds a sample household and prints today's schedule.

Tasks are deliberately added OUT OF ORDER so that the Scheduler's
filter_tasks() and sort_tasks() methods can be seen working in the terminal.
"""

from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task


def build_household(today: date) -> Owner:
    """Create a sample owner with two pets and tasks added in scrambled order."""
    owner = Owner(name="Marcos", available_minutes=90, day_start="08:00")

    biscuit = Pet(name="Biscuit", species="dog", breed="Golden Retriever")
    # Added last-first on purpose: evening before morning, medium before high.
    biscuit.add_task(Task("Evening walk", 25, priority="medium",
                          category="walk", preferred_time="18:00"))
    biscuit.add_task(Task("Morning walk", 30, priority="high",
                          category="walk", preferred_time="07:30"))
    biscuit.add_task(Task("Breakfast", 10, priority="high",
                          category="feeding", preferred_time="08:00"))
    # Same pet, same time as Breakfast -> detect_time_conflicts() should warn.
    biscuit.add_task(Task("Meds", 5, priority="high",
                          category="meds", preferred_time="08:00"))

    luna = Pet(name="Luna", species="cat", breed="Siamese")
    # Low priority first, high priority last - again, out of order.
    luna.add_task(Task("Play session", 20, priority="low",
                       category="enrichment", preferred_time="afternoon"))
    luna.add_task(Task("Nail trim", 15, priority="low",
                       category="grooming", frequency="weekly"))
    luna.add_task(Task("Litter box", 10, priority="high",
                       category="grooming", preferred_time="09:00"))
    # Different pet, same time as Biscuit's Breakfast -> also a conflict.
    luna.add_task(Task("Breakfast", 10, priority="high",
                       category="feeding", preferred_time="08:00"))

    # Already done today -> filter_tasks() should drop it from the plan, and
    # complete_task() adds next week's Nail trim automatically.
    luna.complete_task("Nail trim", today)

    owner.add_pet(biscuit)
    owner.add_pet(luna)
    return owner


def describe(pair) -> str:
    """One-line description of a (pet, task) pair."""
    pet, task = pair
    when = task.preferred_time or "no preference"
    if task.completed:
        status = "done"
    elif task.due_date:
        status = f"due {task.due_date.isoformat()}"
    else:
        status = "due now"
    return (f"{task.title:<16}{pet.name:<10}{task.priority:<9}"
            f"{task.duration_minutes:>3} min   {when:<14}{status}")


def print_section(title: str, pairs) -> None:
    """Print a labelled list of (pet, task) pairs."""
    print(f"\n{title}")
    print("-" * 64)
    if not pairs:
        print("  (none)")
    for pair in pairs:
        print("  " + describe(pair))


def print_schedule(plan, owner) -> None:
    """Print the daily plan as a readable terminal report."""
    width = 64
    print("\n" + "=" * width)
    print(f"TODAY'S SCHEDULE - {plan.day.strftime('%A, %B %d, %Y')}")
    print(f"Owner: {owner.name}   |   Time available: {owner.available_minutes} min")
    print("=" * width)

    if not plan.entries:
        print("  Nothing scheduled today.")
    else:
        print(f"{'TIME':<14}{'TASK':<20}{'PET':<10}{'PRIORITY':<10}{'MIN':>4}")
        print("-" * width)
        for e in plan.entries:
            print(f"{e.start_time + '-' + e.end_time:<14}"
                  f"{e.task.title:<20}"
                  f"{e.pet.name:<10}"
                  f"{e.task.priority:<10}"
                  f"{e.task.duration_minutes:>4}")

    print("-" * width)
    used = plan.total_minutes()
    print(f"Scheduled: {used} min of {owner.available_minutes} min "
          f"({owner.available_minutes - used} min free)")

    if plan.skipped:
        print("\nSKIPPED (ran out of time)")
        for e in plan.skipped:
            print(f"  - {e.task.title} ({e.pet.name}): {e.reason}")
    print("=" * width)


def main() -> None:
    today = date.today()
    owner = build_household(today)
    scheduler = Scheduler(owner)

    # Step 1: raw order, exactly as the tasks were added.
    entered = owner.get_all_tasks()
    print_section("1. TASKS AS ENTERED (unordered)", entered)

    # Step 2: filter_tasks() drops anything not due today.
    due = scheduler.filter_tasks(entered, today)
    print_section("2. AFTER filter_tasks() - only tasks due today", due)
    dropped = [p for p in entered if p not in due]
    for pet, task in dropped:
        reason = ("already completed today" if task.completed
                  else f"next occurrence, due {task.due_date.isoformat()}")
        print(f"  filtered out: {task.title} ({pet.name}) - {reason}")

    # Step 3: sort_tasks() orders by priority, then preferred time, then duration.
    ordered = scheduler.sort_tasks(due)
    print_section("3. AFTER sort_tasks() - high priority and earlier times first", ordered)

    # Step 4: warn about tasks that ask for overlapping times. This only
    # prints warnings; the scheduler still builds a plan by moving tasks.
    print("\n4. detect_time_conflicts() - tasks asking for overlapping times")
    print("-" * 64)
    conflicts = scheduler.detect_time_conflicts(due)
    if not conflicts:
        print("  No conflicts.")
    for warning in conflicts:
        print(f"  WARNING: {warning}")

    # Step 5: the finished plan, with a final check that nothing overlaps.
    plan = scheduler.generate_plan(today)
    print_schedule(plan, owner)
    plan_conflicts = scheduler.detect_conflicts(plan)
    print("Final plan overlaps: " + ("; ".join(plan_conflicts) or "none"))

    # Step 6: completing a recurring task schedules its next occurrence.
    next_breakfast = scheduler.mark_task_complete("Biscuit", "Breakfast", today)
    print_section("6. AFTER mark_task_complete('Biscuit', 'Breakfast') - Biscuit's tasks",
                  [(owner.pets[0], t) for t in owner.pets[0].get_tasks()])
    print(f"  Breakfast is daily, so the next one is due "
          f"{today.isoformat()} + 1 day = {next_breakfast.due_date.isoformat()}")
    print()


if __name__ == "__main__":
    main()
