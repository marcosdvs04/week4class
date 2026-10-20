# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

Output of `python3 main.py`:

```

1. TASKS AS ENTERED (unordered)
----------------------------------------------------------------
  Evening walk    Biscuit   medium    25 min   18:00         due now
  Morning walk    Biscuit   high      30 min   07:30         due now
  Breakfast       Biscuit   high      10 min   08:00         due now
  Meds            Biscuit   high       5 min   08:00         due now
  Play session    Luna      low       20 min   afternoon     due now
  Nail trim       Luna      low       15 min   no preference done
  Litter box      Luna      high      10 min   09:00         due now
  Breakfast       Luna      high      10 min   08:00         due now
  Nail trim       Luna      low       15 min   no preference due 2026-10-27

2. AFTER filter_tasks() - only tasks due today
----------------------------------------------------------------
  Evening walk    Biscuit   medium    25 min   18:00         due now
  Morning walk    Biscuit   high      30 min   07:30         due now
  Breakfast       Biscuit   high      10 min   08:00         due now
  Meds            Biscuit   high       5 min   08:00         due now
  Play session    Luna      low       20 min   afternoon     due now
  Litter box      Luna      high      10 min   09:00         due now
  Breakfast       Luna      high      10 min   08:00         due now
  filtered out: Nail trim (Luna) - already completed today
  filtered out: Nail trim (Luna) - next occurrence, due 2026-10-27

3. AFTER sort_tasks() - high priority and earlier times first
----------------------------------------------------------------
  Morning walk    Biscuit   high      30 min   07:30         due now
  Meds            Biscuit   high       5 min   08:00         due now
  Breakfast       Biscuit   high      10 min   08:00         due now
  Breakfast       Luna      high      10 min   08:00         due now
  Litter box      Luna      high      10 min   09:00         due now
  Evening walk    Biscuit   medium    25 min   18:00         due now
  Play session    Luna      low       20 min   afternoon     due now

4. detect_time_conflicts() - tasks asking for overlapping times
----------------------------------------------------------------
  WARNING: Conflict, same pet (Biscuit): Breakfast (Biscuit, 08:00-08:10) overlaps Meds (Biscuit, 08:00-08:05)
  WARNING: Conflict, different pets: Breakfast (Biscuit, 08:00-08:10) overlaps Breakfast (Luna, 08:00-08:10)
  WARNING: Conflict, different pets: Meds (Biscuit, 08:00-08:05) overlaps Breakfast (Luna, 08:00-08:10)

================================================================
TODAY'S SCHEDULE - Tuesday, October 20, 2026
Owner: Marcos   |   Time available: 90 min
================================================================
TIME          TASK                PET       PRIORITY   MIN
----------------------------------------------------------------
08:00-08:30   Morning walk        Biscuit   high        30
08:30-08:35   Meds                Biscuit   high         5
08:35-08:45   Breakfast           Biscuit   high        10
08:45-08:55   Breakfast           Luna      high        10
09:00-09:10   Litter box          Luna      high        10
18:00-18:25   Evening walk        Biscuit   medium      25
----------------------------------------------------------------
Scheduled: 90 min of 90 min (0 min free)

SKIPPED (ran out of time)
  - Play session (Luna): needs 20 min but only 0 min left
================================================================
Final plan overlaps: none

6. AFTER mark_task_complete('Biscuit', 'Breakfast') - Biscuit's tasks
----------------------------------------------------------------
  Evening walk    Biscuit   medium    25 min   18:00         due now
  Morning walk    Biscuit   high      30 min   07:30         due now
  Breakfast       Biscuit   high      10 min   08:00         done
  Meds            Biscuit   high       5 min   08:00         due now
  Breakfast       Biscuit   high      10 min   08:00         due 2026-10-21
  Breakfast is daily, so the next one is due 2026-10-20 + 1 day = 2026-10-21
```

## 🧪 Testing PawPal+

Run the test suite from the project folder:

```bash
python -m pytest
```

The tests are in `tests/test_pawpal.py` (24 tests). They use fixed dates, so the results don't depend on what day you run them. They cover:

- **Sorting:** `sort_by_time()` returns tasks in chronological order, including `"00:00"`, and tasks at the same time keep the order they were added. The finished plan lists entries by start time, even though high priority tasks are placed first.
- **Filtering:** `filter_by()` works by pet name, by completion status, and by both together. Tasks that are done or not due yet are left out of the plan.
- **Recurrence:** completing a daily task creates a new task due the next day. That task is missing from today's plan and appears in tomorrow's. A weekly task isn't due on day 6 but is due on day 7, including across a month boundary. Completing a task for an unknown pet raises an error.
- **Conflict detection:** two tasks at exactly the same time are flagged. So are overlapping windows, for the same pet or for different pets, and `"morning"` clashing with `"08:00"`. Back-to-back tasks and tasks with no preferred time are not flagged. A generated plan never contains overlaps.
- **Edge cases:** an owner with no pets or a pet with no tasks, a zero time budget, a task that would run past midnight, a preferred time before the owner's day starts, and invalid times such as `"25:00"`, `"12:60"` or `"noon"`.

Successful run:

```
============================= test session starts ==============================
platform darwin -- Python 3.13.0, pytest-9.1.1, pluggy-1.7.0
rootdir: /Users/marcosdelvado/Documents/FAU/Clases/Fall 2026/CEN 4010 Software Engineering/Assignments/week4class
collected 24 items

tests/test_pawpal.py ........................                            [100%]

============================== 24 passed in 0.02s ==============================
```

**Confidence level: ★★★★☆ (4/5)**

The core scheduling rules are well covered, with happy paths and edge cases for sorting, filtering, recurrence and conflicts, and every test passes. Writing these tests also caught a real bug: `"12:60"` was being accepted as a valid time. It isn't 5 stars because:

- The Streamlit UI in `app.py` isn't tested.
- Multi-day scenarios are only partly tested, beyond "today and tomorrow".
- Completing the same daily task twice on one day completes tomorrow's copy early. The schedule is still right, but the history gets an extra "done" record.

## 📐 Smarter Scheduling

On top of the basic plan, the `Scheduler` can sort and filter tasks, repeat daily and weekly tasks, and warn about time conflicts. All of this logic lives in `pawpal_system.py`. Each method below works on `(pet, task)` pairs from `Owner.get_all_tasks()`, so every task stays linked to its pet.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()`, `Scheduler.sort_tasks()` | By preferred time; or by priority, then time, then duration |
| Filtering | `Scheduler.filter_by()`, `Scheduler.filter_tasks()` | By pet name and/or completion status; or only tasks due today |
| Conflict handling | `Scheduler.detect_time_conflicts()`, `Scheduler.detect_conflicts()` | Overlapping time windows, same pet or different pets; warns, never crashes |
| Recurring tasks | `Task.mark_complete()`, `Pet.complete_task()`, `Scheduler.mark_task_complete()` | Completing a task creates the next occurrence: +1 day (daily) or +7 days (weekly) |

### Sorting

- **`Scheduler.sort_by_time(tasks)`** puts tasks in order of preferred time, earliest first. It uses `sorted()` with a lambda key that turns each time into minutes after midnight. That way `"HH:MM"` times and named times (`"morning"` = 08:00, `"afternoon"` = 12:00, `"evening"` = 17:00) sort together correctly. The key is a tuple, `(no preferred time?, minutes)`, so tasks with no preferred time go last.
- **`Scheduler.sort_tasks(tasks)`** is the order `generate_plan()` uses: higher priority first, then earlier preferred time, then shorter duration. Higher-priority tasks claim their time slots first.

### Filtering

- **`Scheduler.filter_by(tasks, day, pet_name=None, completed=None)`** keeps the tasks that match a pet name, a completion status, or both. Any filter left as `None` is ignored. For example, `filter_by(tasks, today, pet_name="Luna", completed=False)` returns Luna's pending tasks.
- **`Scheduler.filter_tasks(tasks, day)`** keeps only the tasks that are due on that day, using `Task.is_due_today()`. `generate_plan()` uses it to drop tasks that are already done and occurrences that aren't due yet.

### Recurring tasks

- **`Task.mark_complete(day)`** marks the task done and returns a new copy for the next occurrence. The copy is due on `Task.next_due_date(day)`, which is `day + timedelta(days=1)` for daily tasks and `day + timedelta(days=7)` for weekly ones. Using `timedelta` means month and year boundaries are handled for you, so a weekly task done on Oct 28 is next due Nov 4.
- **`Pet.complete_task(title, day)`** completes the pet's pending task with that title and adds the next occurrence to the pet's task list. The completed copy stays in the list as history.
- **`Scheduler.mark_task_complete(pet_name, title, day)`** does the same thing, looking up the pet by name.
- A new occurrence stays out of the plan until its due date, because `Task.is_due_today()` checks `due_date`.

### Conflict detection

- **`Scheduler.detect_time_conflicts(tasks)`** checks the times tasks *ask* for, before the plan is built. Each task with a preferred time asks for the window from its preferred time to preferred time + duration. The method sorts the windows by start time and compares each one only with the windows that start before it ends. For every overlap it returns a warning string, labelled "same pet" or "different pets." It never raises an error and never changes a task. Back-to-back tasks, where one ends at 08:00 and the next starts at 08:00, are not conflicts. Tasks with no preferred time are not checked.
- **`Scheduler.detect_conflicts(plan)`** runs the same check on a finished `DailyPlan`. `generate_plan()` moves a clashing task to the next free slot, so this should always come back empty. It's there as a safety check.
- Both methods share the helper `Scheduler._overlap_warnings()`.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
