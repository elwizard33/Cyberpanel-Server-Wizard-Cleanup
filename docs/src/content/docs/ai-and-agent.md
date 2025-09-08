---
title: AI & Agent
description: Internal AI assistant architecture
---

# AI & Agent

The agent implements a constrained ReAct loop:
1. System prompt enumerates safe tools.
2. Model proposes tool call OR final answer.
3. Framework validates name & args; executes.
4. Result appended; loop continues until final.

Safety levers: step cap, byte cap, no shell, tool schema validation.

