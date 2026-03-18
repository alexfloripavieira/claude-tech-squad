# Changelog

## 2.4.0

- made `/claude-tech-squad:squad` TDD-first by default for code changes
- required the Test Plan and TDD Delivery Plan to be ready before build starts in squad flows
- made TDD exceptions explicit in squad and implementation reporting
- updated docs to explain the new default behavior

## 2.3.0

- added `tdd-specialist` to drive development from failing tests and red-green-refactor cycles
- added `design-principles-specialist` for SOLID, Clean Architecture, Ports and Adapters, Hexagonal-style boundaries, and testability guardrails
- updated discovery, implement, and squad workflows to include structural guardrails and TDD delivery planning before implementation
- updated public documentation and playbooks to explain the new testing and design-role split

## 2.2.0

- added visible orchestration lines for phase changes, agent handoffs, retries, and parallel batches
- added mandatory `Agent Execution Log` output to discovery, implement, and squad workflows
- documented how visible agent execution appears in Claude output

## 2.1.0

- clarified product positioning versus `claude-config`
- added validation workflow and release documentation
- added license and public-distribution structure

## 2.0.0

- expanded the plugin into a full specialist technology squad
