"""Quick tests for the PawPal+ logic layer."""

from datetime import date

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
