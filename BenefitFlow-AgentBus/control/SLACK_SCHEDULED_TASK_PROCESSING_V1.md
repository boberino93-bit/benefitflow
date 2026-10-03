# BenefitFlow Slack Scheduled Task Processing V1

Status: ACTIVE / HUMAN-DIRECTED
Project: BenefitFlow (`project_id=benefitflow`)

## Purpose

Slack is an approved secondary operational surface for scheduling visibility, task queueing, reminders, status updates, and human-readable coordination around BenefitFlow work.

Slack does **not** replace the BenefitFlow repository, AgentBus forum, accepted state, swarm roster, enhancement cursor, or other durable control artifacts as project truth.

## Authoritative-state rule

- GitHub repository state and `BenefitFlow-AgentBus/` remain authoritative for project identity, role authority, accepted state, research evidence, dispositions, handoffs, approvals, and recovery.
- Slack task/list/message state is operational metadata only.
- A Slack task may point to authoritative repo artifacts, but may not silently change project truth.
- Any material result produced through scheduled Slack processing must be persisted back into the BenefitFlow repo/forum before it is treated as durable project state.

## Approved Slack use

Slack may be used to:
- maintain a scheduled-task queue;
- surface due work and cadence;
- assign operational ownership to Primary, Managers, Research, or Human;
- record lightweight status and last-result summaries;
- schedule reminders/messages for due work;
- surface blocked items requiring human action;
- link back to authoritative BenefitFlow repo/forum artifacts.

## Current queue

Slack List: `BenefitFlow Scheduled Task Queue`
Slack List ID: `F0C6J84HJR0`

The queue includes fields for task, status, cadence, owner role, project, repo/artifact reference, human-approval requirement, and last result.

## Safety and authority boundaries

Scheduled Slack processing must not bypass or weaken:
- project/repository isolation;
- the P0 architecture gate;
- human approval requirements for external booking, financial action, sensitive disclosure, or materially changed terms;
- Manager review before Primary acceptance where required;
- the foreign-repository read-only invariant;
- package parity and recovery synchronization rules.

Slack tasks that require human approval must remain blocked until that approval is explicitly obtained and durably reflected in authoritative BenefitFlow state.

## Processing model

At an active service checkpoint, the responsible agent may read due Slack tasks, reconcile each task against current repository truth, perform the permitted work, persist any material result into BenefitFlow, then update Slack with the resulting status and authoritative artifact reference.

A Slack status of `Complete` is insufficient by itself for any material architecture, research, acceptance, or recovery decision; the corresponding repository/forum evidence must exist.

## Failure handling

If Slack is unavailable, stale, inconsistent with the repo, or contains a task that conflicts with accepted BenefitFlow state, fail closed to repository truth and record the discrepancy when materially relevant.
