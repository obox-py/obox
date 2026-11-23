---
status: draft
---

# <能力名> Spec Delta

## Purpose

<!-- 这次为什么改：一句话讲清缺口或冲突，别写实现。 -->

## ADDED Requirements

### Requirement: <新需求名>

<用 SHALL 陈述新增的可观测行为。>

#### Scenario: <场景名>

- **WHEN** <前置条件>
- **THEN** <可观测结果>

## MODIFIED Requirements

<!-- 只列基线 spec.md 里真实存在、且本次要改的需求；写清改前的位置。 -->

### Requirement: <现有需求名>

<改后的 SHALL 陈述；在下面注明改自基线哪一条。>

#### Scenario: <场景名>

- **WHEN** <前置条件>
- **THEN** <可观测结果>

## REMOVED Requirements

### Requirement: <要删的现有需求名>

- 理由：<为什么不再需要>
- 影响：<谁会受影响>

## RENAMED Requirements

<!-- 只在需要改名时保留本节，否则整节删掉。 -->

- From: `### Requirement: <旧名>`
- To: `### Requirement: <新名>`

## Impact

<!-- 与基线 spec.md 的冲突与兼容性：哪几条现有需求被动到，旧行为还留不留。 -->
