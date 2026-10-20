"""Quick tests for the PawPal+ logic layer."""

from datetime import date

from pawpal_system import Pet, Task


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
