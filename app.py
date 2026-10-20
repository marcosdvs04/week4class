from datetime import date

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task, to_minutes

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# Streamlit reruns this script on every interaction, so keep the Owner in
# session_state and only create it the first time.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_minutes=60)
owner = st.session_state.owner
scheduler = Scheduler(owner)
today = date.today()


def task_status(task: Task) -> str:
    """Short status label for the task table."""
    if task.completed:
        return "✅ done"
    if task.due_date is None or task.due_date <= today:
        return "due today"
    return f"due {task.due_date.strftime('%b %d')}"


def show_flash() -> None:
    """Show a message saved before the last st.rerun(), then clear it."""
    message = st.session_state.pop("flash", None)
    if message:
        st.success(message)


st.title("🐾 PawPal+")
st.caption("Plan your pets' care tasks around the time you have today.")

# --- Owner -------------------------------------------------------------------
st.subheader("Owner")
with st.form("owner_form"):
    name = st.text_input("Owner name", value=owner.name)
    col1, col2 = st.columns(2)
    with col1:
        minutes = st.number_input(
            "Time available today (minutes)", min_value=0, max_value=24 * 60,
            value=owner.available_minutes,
        )
    with col2:
        day_start = st.text_input("Day starts at (HH:MM)", value=owner.day_start)
    if st.form_submit_button("Save owner"):
        try:
            if not 0 <= to_minutes(day_start) < 24 * 60:
                raise ValueError
            owner.name = name
            owner.update_availability(int(minutes))
            owner.day_start = day_start
            st.success("Owner saved.")
        except ValueError:
            st.error("Day start must be a time like 08:00.")

# --- Pets --------------------------------------------------------------------
st.subheader("Pets")
with st.form("pet_form", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with col3:
        breed = st.text_input("Breed (optional)")
    if st.form_submit_button("Add pet"):
        if not pet_name.strip():
            st.error("Enter a pet name.")
        else:
            try:
                owner.add_pet(Pet(name=pet_name.strip(), species=species, breed=breed.strip()))
                st.success(f"Added {pet_name.strip()}.")
            except ValueError as e:
                st.error(str(e))

if not owner.get_pets():
    st.info("No pets yet. Add one above.")

# --- Tasks -------------------------------------------------------------------
if owner.get_pets():
    st.subheader("Tasks")
    with st.form("task_form", clear_on_submit=True):
        pet_choice = st.selectbox("Pet", [p.name for p in owner.get_pets()])
        title = st.text_input("Task title", placeholder="Morning walk")
        col1, col2, col3 = st.columns(3)
        with col1:
            duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        with col2:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        with col3:
            frequency = st.selectbox("Frequency", ["daily", "weekly"])
        col4, col5 = st.columns(2)
        with col4:
            category = st.selectbox(
                "Category", ["walk", "feeding", "meds", "enrichment", "grooming", "general"]
            )
        with col5:
            preferred = st.text_input(
                "Preferred time (optional)", placeholder="08:00 or morning"
            )
        if st.form_submit_button("Add task"):
            pet = next(p for p in owner.get_pets() if p.name == pet_choice)
            if not title.strip():
                st.error("Enter a task title.")
            else:
                try:
                    pet.add_task(Task(
                        title=title.strip(),
                        duration_minutes=int(duration),
                        priority=priority,
                        category=category,
                        preferred_time=preferred.strip() or None,
                        frequency=frequency,
                    ))
                    st.success(f"Added {title.strip()} for {pet.name}.")
                except ValueError as e:
                    st.error(str(e))

    # One table for every pet, sorted by time, with pet and status filters.
    st.markdown("**All tasks** (sorted by preferred time)")
    col1, col2 = st.columns(2)
    with col1:
        pet_filter = st.selectbox("Show pet", ["All pets"] + [p.name for p in owner.get_pets()])
    with col2:
        status_filter = st.radio("Show status", ["All", "Pending", "Done"], horizontal=True)
    shown = scheduler.sort_by_time(scheduler.filter_by(
        owner.get_all_tasks(),
        today,
        pet_name=None if pet_filter == "All pets" else pet_filter,
        completed={"All": None, "Pending": False, "Done": True}[status_filter],
    ))
    if shown:
        st.table([
            {
                "Time": t.preferred_time or "any",
                "Task": t.title,
                "Pet": pet.name,
                "Minutes": t.duration_minutes,
                "Priority": t.priority,
                "Repeats": t.frequency,
                "Status": task_status(t),
            }
            for pet, t in shown
        ])
    elif owner.get_all_tasks():
        st.caption("No tasks match these filters.")
    else:
        st.caption("No tasks yet. Add one above.")

    # Completing a task creates its next daily/weekly occurrence.
    show_flash()
    due_now = scheduler.filter_tasks(owner.get_all_tasks(), today)
    if due_now:
        with st.form("complete_form"):
            labels = [f"{t.title} ({pet.name})" for pet, t in due_now]
            choice = st.selectbox("Mark a task done", labels)
            if st.form_submit_button("Mark complete"):
                pet, t = due_now[labels.index(choice)]
                next_task = scheduler.mark_task_complete(pet.name, t.title, today)
                st.session_state.flash = (
                    f"Marked {t.title} done for {pet.name}. It repeats {t.frequency}, "
                    f"so the next one is due {next_task.due_date.strftime('%A, %B %d')}."
                )
                st.rerun()

# --- Schedule ----------------------------------------------------------------
st.divider()
st.subheader("Today's schedule")

if st.button("Generate schedule", disabled=not owner.get_all_tasks()):
    st.session_state.show_plan = True

# Keep showing the plan after other interactions, so it updates as tasks change.
if st.session_state.get("show_plan") and owner.get_all_tasks():
    plan = scheduler.generate_plan(today)
    placed = {id(e.task): e for e in plan.entries}

    def placed_at(task: Task) -> str:
        """Where the plan put a task, for conflict messages."""
        entry = placed.get(id(task))
        return entry.start_time if entry else "nowhere (it was skipped)"

    # Conflicts first: they explain why some tasks aren't at their preferred time.
    due = scheduler.filter_tasks(owner.get_all_tasks(), today)
    for (pet_a, task_a), (pet_b, task_b) in scheduler.find_time_conflicts(due):
        label_a, label_b = f"{pet_a.name}'s {task_a.title}", f"{pet_b.name}'s {task_b.title}"
        st.warning(
            f"**Time conflict:** {label_a} ({task_a.preferred_time}, "
            f"{task_a.duration_minutes} min) overlaps {label_b} "
            f"({task_b.preferred_time}, {task_b.duration_minutes} min). "
            f"You can only do one at a time, so PawPal+ placed {label_a} at "
            f"{placed_at(task_a)} and {label_b} at {placed_at(task_b)}. "
            f"To keep both on time, change one task's preferred time.",
            icon="⏰",
        )

    st.markdown(f"**{plan.day.strftime('%A, %B %d')}**")
    used, available = plan.total_minutes(), owner.available_minutes
    if plan.entries and not plan.skipped:
        st.success(f"All {len(plan.entries)} tasks fit: {used} of {available} min used.")
    elif plan.skipped:
        st.warning(
            f"{len(plan.skipped)} task(s) didn't fit today. "
            f"{used} of {available} min used. See *Skipped* below."
        )

    if plan.entries:
        st.table([
            {
                "Time": f"{e.start_time}-{e.end_time}",
                "Task": e.task.title,
                "Pet": e.pet.name,
                "Priority": e.task.priority,
                "Why": e.reason,
            }
            for e in plan.entries
        ])
    else:
        st.info("Nothing is due today, or nothing could be scheduled.")

    if plan.skipped:
        st.markdown("**Skipped**")
        st.table([
            {"Task": e.task.title, "Pet": e.pet.name, "Priority": e.task.priority,
             "Why": e.reason}
            for e in plan.skipped
        ])

    # Safety check: the scheduler should never overlap tasks in the plan itself.
    for warning in scheduler.detect_conflicts(plan):
        st.error(warning)
