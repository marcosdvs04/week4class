# PawPal+ Project Reflection

## 1. System Design

**Core user actions**

Based on the scenario, I identified three core actions a user should be able to perform in PawPal+:

1. **Set up an owner and pet profile.** The user enters basic information about themselves and their pet, such as the owner's name, how much time they have available in the day, and any care preferences, along with the pet's name and species or breed. This comes first because the owner's available time is the main constraint the scheduler has to work within.
2. **Add and edit care tasks.** The user creates the care tasks their pet needs, such as a morning walk, feeding, or giving medication. Each task has at least a duration and a priority, and it may also have a category, a preferred time of day, or a frequency like daily or weekly. The user can update or remove tasks as their routine changes, and these tasks are the input the scheduler works from.
3. **Generate and view today's plan.** The user asks the app to build a daily schedule. The app orders tasks by priority, fits them into the time available, and leaves out tasks that don't fit. It then shows the plan as a clear, timed list and explains its choices, for example why medication was scheduled first or why grooming was skipped because time ran out.

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

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
