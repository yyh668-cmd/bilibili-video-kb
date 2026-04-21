# Memory Bank Guide

This folder is the project memory that survives across Codex threads.

## Read This First

If you open a fresh thread, tell Codex to read:

1. `AGENTS.md`
2. `memory-bank/README.md`
3. `memory-bank/activeContext.md`
4. `memory-bank/tasks.md`
5. `memory-bank/progress.md`

That gives a new thread enough context to continue the project without depending on old chat history.

## What Each File Does

- `projectbrief.md`: the stable mission of the project.
- `productContext.md`: who the project is for and what experience it should create.
- `systemPatterns.md`: architecture and workflow rules that should stay stable.
- `techContext.md`: stack, commands, and important files.
- `tasks.md`: the current backlog and task status.
- `activeContext.md`: the current focus, open questions, blockers, and next action.
- `progress.md`: a running log of milestones and recent changes.
- `decisionLog.md`: important decisions and why they were made.

## Simple Beginner Workflow

### 1. Start a new task

Ask Codex:

`Read AGENTS.md and the memory-bank files, then continue from the current state.`

### 2. During the task

If the work becomes long or confusing, ask Codex:

`Before continuing, update activeContext.md and progress.md so we do not lose the thread.`

### 3. End the task

Ask Codex:

`Close the loop by updating the memory bank: activeContext, tasks, progress, and any decisions.`

## When To Start A Fresh Thread

Start a new thread when:

- the chat has become long and messy
- Codex starts forgetting rules or repeating work
- one milestone is done and the next step is clear
- you want to split work into smaller tasks

The correct pattern is not "one forever thread." The correct pattern is "many clean threads connected by shared files."
