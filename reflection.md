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

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

My conflict detection only warns about clashes. It doesn't resolve them in a smart way. `Scheduler.detect_time_conflicts()` looks at the time window each task asks for (its preferred time plus its duration) and reports any two windows that overlap, whether they belong to the same pet or to different pets. It returns these as warning messages instead of raising an error. When the plan is built, the conflict is settled by a simple rule. Tasks are placed one at a time in sorted order: higher priority first, then earlier preferred time, then shorter duration. The task placed first keeps its slot, and each later task moves to the next free slot. For example, Biscuit's breakfast, Biscuit's meds, and Luna's breakfast all want 08:00. The scheduler warns about all three clashes. The morning walk (07:30, moved to 08:00 because the day starts then) has already taken 08:00-08:30, so the three tasks are placed one after another starting at 08:30, and Luna's breakfast ends up at 08:45. The scheduler never looks for a better arrangement, such as moving a lower priority task earlier or asking the owner which task should give way. It also only checks tasks that have a preferred time, so a task with no time preference can never be part of a conflict warning.

This tradeoff is reasonable for PawPal+ because a pet owner usually has only a handful of tasks a day, and most clashes are small, like two feedings at the same time. In that situation, a clear warning plus a predictable "next free slot" rule is easier to understand and trust than an optimizer that rearranges the whole day. Returning warnings instead of crashing also means the owner still gets a usable plan and can fix the clash themselves by changing a preferred time. Using overlapping windows instead of exact time matches costs almost nothing extra and catches real problems an exact match would miss, like a 30-minute walk at 07:45 running into breakfast at 08:00.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
