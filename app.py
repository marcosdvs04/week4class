from datetime import date

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task, to_minutes

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# Streamlit reruns this script on every interaction, so keep the Owner in
# session_state and only create it the first time.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_minutes=60)
owner = st.session_state.owner

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

    for pet in owner.get_pets():
        st.markdown(f"**{pet.name}** ({pet.species}{', ' + pet.breed if pet.breed else ''})")
        tasks = pet.get_tasks()
        if tasks:
            st.table([
                {
                    "Task": t.title,
                    "Minutes": t.duration_minutes,
                    "Priority": t.priority,
                    "Category": t.category,
                    "Preferred": t.preferred_time or "-",
                    "Frequency": t.frequency,
                }
                for t in tasks
            ])
        else:
            st.caption("No tasks yet.")

# --- Schedule ----------------------------------------------------------------
st.divider()
st.subheader("Today's schedule")

if st.button("Generate schedule", disabled=not owner.get_all_tasks()):
    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan(date.today())

    st.markdown(
        f"**{plan.day.strftime('%A, %B %d')}** - {plan.total_minutes()} of "
        f"{owner.available_minutes} min scheduled"
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
        st.info("Nothing could be scheduled today.")

    if plan.skipped:
        st.markdown("**Skipped**")
        for e in plan.skipped:
            st.markdown(f"- {e.task.title} ({e.pet.name}): {e.reason}")

    for warning in scheduler.detect_conflicts(plan):
        st.warning(warning)
