# Experiment Ledger Skill

## Purpose

Use this skill whenever a project needs to test a hypothesis against one or more baselines and preserve a reproducible, machine-readable research record.

The skill separates **experimental evidence** from **interpretation**. It does not decide that a target system is better. It records what was declared, what ran, what happened, what failed, and what evidence supports later analysis.

## Core invariant

> Never let analysis overwrite evidence.

The lifecycle is:

```text
hypothesis -> manifest -> declared baselines -> execution -> raw evidence -> normalized measurements -> comparison -> interpretation