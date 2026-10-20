# PawPal+ Project Reflection

## 1. System Design

**Core user actions**

Based on the scenario, I identified three core actions a user should be able to perform in PawPal+:

1. **Set up an owner and pet profile.** The user enters basic information about themselves and their pet, such as the owner's name, how much time they have available in the day, and any care preferences, along with the pet's name and species or breed. This comes first because the owner's available time is the main constraint the scheduler has to work within.
2. **Add and edit care tasks.** The user creates the care tasks their pet needs, such as a morning walk, feeding, or giving medication. Each task has at least a duration and a priority, and it may also have a category, a preferred time of day, or a frequency like daily or weekly. The user can update or remove tasks as their routine changes, and these tasks are the input the scheduler works from.
3. **Generate and view today's plan.** The user asks the app to build a daily schedule. The app orders tasks by priority, fits them into the time available, and leaves out tasks that don't fit. It then shows the plan as a clear, timed list and explains its choices, for example why medication was scheduled first or why grooming was skipped because time ran out.

**a. Initial design**

My initial UML design has six classes organized around a simple flow: an owner has pets, each pet has care tasks, and a scheduler turns those tasks into a daily plan. I kept the data objects (`Owner`, `Pet`, `Task`, `ScheduledTask`, `DailyPlan`) as Python dataclasses and made `Scheduler` a regular class, since it holds behavior rather than data.

- **Owner** stores the person's name, how many minutes they have for pet care today, what time their day starts, and any preferences. It is responsible for managing the list of pets and supplies the main constraint the scheduler works within: available time.
- **Pet** stores the pet's name, species, and breed, and owns its list of care tasks. It is responsible for adding, editing, and removing those tasks.
- **Task** represents a single care activity such as a walk, feeding, or medication. It holds the title, duration, priority, category, preferred time, and how often it repeats. It is responsible for reporting its own priority as a number for sorting and for deciding whether it is due on a given day.
- **Scheduler** contains the planning logic. It reads the owner's constraints, filters out tasks that aren't due, sorts the rest by priority, fits them into the available time, and checks for conflicts. Its main method, `generate_plan`, produces a `DailyPlan`.
- **DailyPlan** is the output for one day. It keeps the list of scheduled entries and a separate list of skipped tasks, and it can total the scheduled minutes and produce a readable summary for the UI.
- **ScheduledTask** is one entry in the plan. It links a task to its pet, adds a start and end time, and stores the reason it was scheduled or skipped. Keeping it separate from `Task` means the same task can appear in plans on different days without changing the task itself.

**b. Design changes**

Yes. After drafting the skeleton, I asked my AI assistant to review `pawpal_system.py` for missing relationships and logic bottlenecks, and I made two changes based on its feedback:

1. **Keeping the pet attached to each task during scheduling.** Originally, `Scheduler.sort_tasks()` and `filter_tasks()` took a plain list of `Task` objects. The problem is that once tasks from several pets are combined and sorted, there is no way to know which pet each task belongs to, but `DailyPlan.add_entry()` needs that information. I added an `Owner.get_all_tasks()` method that returns `(pet, task)` pairs and changed the scheduler methods to work with those pairs instead.
2. **Replacing `completed` with `last_completed`.** Originally, `Task` had a `completed: bool` flag. That doesn't work for recurring tasks: once a daily walk is marked done, it would stay done forever and never appear in tomorrow's plan. I replaced the flag with `last_completed`, a date, so `is_due_today()` can compare it to the current day and decide whether a daily or weekly task is due again.

The review also pointed out a few things I decided not to change yet: times are stored as strings like `"08:00"`, which will need parsing for time math; tasks are identified by title, which could be ambiguous if a pet has two tasks with the same name; and `priority` and `preferences` aren't validated. These are manageable at the current size of the project, and I will revisit them if they cause problems during implementation.

**Later change (Phase 3).** When I added automatic recurrence, a `completed` flag came back, but in a different form. Marking a task complete now marks *that occurrence* done and creates a new `Task` for the next occurrence, with a `due_date` one day or seven days later. So `completed` no longer means "done forever". It means "this specific occurrence is done", and `due_date` decides when the next one shows up. This also forced me to deal with the title issue from the review: a pet can now have a completed "Breakfast" and a pending "Breakfast", so `add_task()` only rejects duplicate titles among pending tasks, and `_find_task()` returns the pending one first. The final UML in `diagrams/uml_final.mmd` shows these changes.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

My scheduler considers these constraints:

- **Time available.** The owner's `available_minutes` is a hard limit. A task that would go over it is skipped, never squeezed in.
- **Day start and midnight.** Nothing is placed before the owner's `day_start` or allowed to run past midnight.
- **Priority.** High, medium, low. Higher priority tasks are placed first, so they claim their time slots and the time budget first.
- **Preferred time.** Either a clock time like `"08:00"` or a part of the day like `"morning"`. This is a soft constraint: a task starts at its preferred time if that slot is free, otherwise at the next free slot after it.
- **Frequency and due date.** Only tasks that are due today are scheduled. Done tasks, and next occurrences that aren't due yet, are filtered out first.
- **Duration** is used to break ties: within the same priority and preferred time, shorter tasks go first.

I ranked them by what goes wrong when each one is ignored. Going over the owner's time makes the plan useless, because the owner simply can't do it, so time is a hard limit. Missing a high priority task like medication matters more than a play session happening late, so priority decides the order. Preferred times matter least: a walk at 08:30 instead of 08:00 is usually fine, so the scheduler moves tasks rather than dropping them, and the "Why" column explains the move. The `preferences` dictionary on `Owner` is not used by the scheduler yet. Priority and preferred time covered everything the scenario needed.

**b. Tradeoffs**

My conflict detection only warns about clashes. It doesn't resolve them in a smart way. `Scheduler.detect_time_conflicts()` looks at the time window each task asks for (its preferred time plus its duration) and reports any two windows that overlap, whether they belong to the same pet or to different pets. It returns these as warning messages instead of raising an error. When the plan is built, the conflict is settled by a simple rule. Tasks are placed one at a time in sorted order: higher priority first, then earlier preferred time, then shorter duration. The task placed first keeps its slot, and each later task moves to the next free slot. For example, Biscuit's breakfast, Biscuit's meds, and Luna's breakfast all want 08:00. The scheduler warns about all three clashes. The morning walk (07:30, moved to 08:00 because the day starts then) has already taken 08:00-08:30, so the three tasks are placed one after another starting at 08:30, and Luna's breakfast ends up at 08:45. The scheduler never looks for a better arrangement, such as moving a lower priority task earlier or asking the owner which task should give way. It also only checks tasks that have a preferred time, so a task with no time preference can never be part of a conflict warning.

This tradeoff is reasonable for PawPal+ because a pet owner usually has only a handful of tasks a day, and most clashes are small, like two feedings at the same time. In that situation, a clear warning plus a predictable "next free slot" rule is easier to understand and trust than an optimizer that rearranges the whole day. Returning warnings instead of crashing also means the owner still gets a usable plan and can fix the clash themselves by changing a preferred time. Using overlapping windows instead of exact time matches costs almost nothing extra and catches real problems an exact match would miss, like a 30-minute walk at 07:45 running into breakfast at 08:00.

---

## 3. AI Collaboration

**a. How you used AI**

I used Claude Code as a coding assistant in every phase:

- **Design.** Reviewing my UML skeleton for missing relationships, which led to the `(pet, task)` pairs.
- **Planning.** Reviewing `main.py` to suggest a short list of algorithm improvements before Phase 3.
- **Implementation.** Sorting, filtering, recurrence and conflict detection.
- **Testing.** Planning edge cases and drafting the tests.
- **Final phase.** Updating the Streamlit UI, the final UML and this documentation.

The features that were most effective for building the scheduler:

- **Edits across several files at once.** Recurrence touched `Task`, `Pet`, `Scheduler`, `main.py` and the tests together. Having the assistant make all of those changes and then run the tests kept everything consistent.
- **Running code in the terminal, not just writing it.** The assistant ran `python -m pytest` and `main.py` after each change, and it ran the Streamlit app headlessly to check the UI. Because of that, its answers were based on real output, not guesses.
- **Explanations of Python features** I hadn't used much: a lambda that returns a tuple as a `sorted()` key, `timedelta` for date math, `dataclasses.replace()`, and `pytest.mark.parametrize`.

The most helpful prompts were specific and gave the assistant the right file and a constraint. Examples: "a *lightweight* conflict detection strategy that returns a warning instead of crashing", "how do I use a lambda as a key to sort `HH:MM` strings", and, when a test failed, "is the bug in my test or in my logic?". That last question found a real bug: `"12:60"` was accepted as a valid time because the validation only checked the total minutes, not hours and minutes separately.

**b. Judgment and verification**

There were two suggestions I didn't accept as-is:

1. **The `main.py` demo.** For the sorting and filtering step, the assistant wrote a `main.py` that printed several lists using `sort_by_time()` and `filter_by()`. I replaced it with my own version. It walks through the same steps `generate_plan()` uses, in numbered order: tasks as entered (deliberately out of order), then after `filter_tasks()`, then after `sort_tasks()`, then the final plan. I wanted the demo to show how the plan is built, not just that the helper methods work. The assistant then built on my version for the conflict and recurrence steps, instead of going back to its own.
2. **A "more Pythonic" conflict check.** When I asked how to simplify the conflict sweep, the assistant suggested `itertools.combinations` instead of my nested loop with an early `break`. The shorter version gives the same results, but it checks every pair, and it hides *why* the list is sorted (sorting only matters because of the `break`). A reader could delete the sort without realizing it changes the behavior. I kept the loop, because its docstring explains the idea and a person can follow it line by line.

To verify suggestions, I relied on running things rather than trusting explanations: the test suite after every change, `main.py` to see the real schedule, and the git diff before committing. This mattered more than once. A draft of my tradeoff paragraph said "the higher priority task keeps its slot", but in the real output all the clashing tasks were high priority and the walk took 08:00 first, so the wording had to change. A draft README walkthrough claimed a task would be skipped with 90 minutes available; running that exact scenario showed it fit, so the example was changed to 60 minutes.

**c. AI strategy and organizing the work**

I used a mix of separate and combined chat sessions. The early design work, from the scenario to the UML and the class skeletons, happened in its own session. The algorithm, testing and final-polish phases mostly ran in one longer session, which I kept organized by giving one assignment step at a time and checking the result before moving on.

Separate sessions helped by keeping each one focused. The design chat was only about classes and relationships, so its suggestions weren't mixed up with implementation details. Starting a new chat also forced me to re-attach the current files, so the assistant worked from the code as it really was, not from an older version it remembered. The longer combined session had the opposite strength: the assistant remembered earlier decisions, like the `(pet, task)` pairs and the recurrence design, so later steps built on them without re-explaining. Its downside was that I had to watch for the assistant assuming a file still looked the way it had left it. For example, I had rewritten `main.py` and committed changes in between, and it was important that the assistant re-read the files before editing.

---

## 4. Testing and Verification

**a. What you tested**

The suite in `tests/test_pawpal.py` has 25 tests, using fixed dates so results don't depend on the day they run:

- **Sorting:** `sort_by_time()` is chronological (including `"00:00"`) and keeps ties in the order they were added, and the finished plan is listed by start time.
- **Filtering:** by pet, by completion status, and by both together.
- **Recurrence:** completing a daily task removes it from today's plan and puts a new one in tomorrow's. A weekly task isn't due on day 6 but is due on day 7, including across a month boundary.
- **Conflicts:** exact duplicate times, partial overlaps, same pet vs. different pets, `"morning"` vs. `"08:00"`. Back-to-back tasks are *not* flagged, and the generated plan itself never overlaps.
- **Edge cases:** an owner with no pets, a pet with no tasks, a zero time budget, a task that would run past midnight, a preferred time before the day starts, invalid times, and an unknown pet name.

These tests matter because the scheduler's rules interact. A change to sorting changes which task gets a slot, and a change to recurrence changes what's "due". The tests let me refactor, like splitting the conflict sweep for the UI, and know straight away whether I broke something. They also caught a real validation bug (`"12:60"`).

**b. Confidence**

I'd rate my confidence at 4 out of 5. The core rules are tested on happy paths and edge cases, and everything passes. I also checked the Streamlit app with a headless run that filtered tasks, generated a plan with conflicts, and marked a task complete. It isn't 5 out of 5 because the UI checks aren't part of the automated suite, and some multi-day behavior is only partly tested.

If I had more time, I would test next:

- completing the same daily task twice on one day (it currently completes tomorrow's occurrence early),
- a week of plans in a row, with tasks completed on some days and not others,
- many tasks requesting the same time,
- the greedy budget case, where one long high priority task uses up time that two shorter tasks could have shared,
- automated Streamlit tests using `AppTest`.

---

## 5. Reflection

**a. What went well**

I'm most satisfied with how conflict detection turned out from start to finish. The first version only checked the finished plan, which could never contain an overlap, so it never reported anything. Rethinking it to check the times tasks *ask* for made it actually useful. In the UI, each warning now tells the owner which tasks clash, where PawPal+ placed each one, and how to fix it. I also like that the logic layer stayed clean: `app.py` and `main.py` only call `Scheduler` methods, and all of the rules live in `pawpal_system.py`, where the tests cover them.

**b. What you would improve**

- **Identify tasks by an id instead of their title.** Titles worked at first, but recurrence made them awkward, because one pet can have a completed and a pending task with the same name.
- **Make the time budget smarter.** It's greedy, so a long high priority task can push out two shorter tasks that would have fit together.
- **Save the owner's data.** It lives in Streamlit's session state, so it disappears when the page reloads.
- **Use the owner's `preferences`,** or remove the field.
- **Complete only tasks that are due.** Right now, completing a task that isn't due yet completes tomorrow's occurrence early.

**c. Key takeaway**

Being the "lead architect" means the AI can write a lot of correct code quickly, but I'm still the one who decides what the system *is*. The assistant was fastest and most useful when I had already made the design decisions: what a conflict means, that warnings shouldn't crash the app, and that the demo should show the scheduling pipeline. It was least useful when I let it decide things that depend on the purpose of the project. My job was to keep the design consistent, to check every claim against real output, and to say no to suggestions that were clever but harder to understand. The tests and the UML were how I kept that control: the tests told me the code still did what I meant, and updating the UML showed me whether the design had drifted from my plan.
