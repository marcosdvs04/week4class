"""PawPal+ demo script: builds a sample household and prints today's schedule."""

from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task


def build_household() -> Owner:
    """Create a sample owner with two pets and several care tasks."""
    owner = Owner(name="Marcos", available_minutes=120, day_start="08:00")

    biscuit = Pet(name="Biscuit", species="dog", breed="Golden Retriever")
    biscuit.add_task(Task("Morning walk", 30, priority="high",
                          category="walk", preferred_time="07:30"))
    biscuit.add_task(Task("Breakfast", 10, priority="high",
                          category="feeding", preferred_time="08:00"))
    biscuit.add_task(Task("Evening walk", 25, priority="medium",
                          category="walk", preferred_time="18:00"))

    luna = Pet(name="Luna", species="cat", breed="Siamese")
    luna.add_task(Task("Litter box", 10, priority="high",
                       category="grooming", preferred_time="09:00"))
    luna.add_task(Task("Play session", 20, priority="low",
                       category="enrichment", preferred_time="afternoon"))
    luna.add_task(Task("Nail trim", 15, priority="low",
                       category="grooming", frequency="weekly"))

    owner.add_pet(biscuit)
    owner.add_pet(luna)
    return owner


def print_schedule(plan, owner) -> None:
    """Print the daily plan as a readable terminal report."""
    width = 64
    print()
    print("=" * width)
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
        print()
        print("SKIPPED")
        for e in plan.skipped:
            print(f"  - {e.task.title} ({e.pet.name}): {e.reason}")
    print("=" * width)
    print()


def main() -> None:
    owner = build_household()
    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan(date.today())
    print_schedule(plan, owner)

    conflicts = scheduler.detect_conflicts(plan)
    if conflicts:
        print("CONFLICTS DETECTED:")
        for warning in conflicts:
            print(f"  ! {warning}")
        print()


if __name__ == "__main__":
    main()
