---
name: df-delta-spec
description: 针对一条 US 变更，读取工程基线的 spec.md，盘问本次与基线的需求冲突，创建或更新该变更的 delta-spec.md。
---

df-delta-spec 产出一份东西：`{df_change_dir}/delta-spec.md`——本次变更相对基线 `spec.md` 的需求差异。不改代码，不写 design。

## 变量

| 变量 | 用途 | 说明 |
|---|---|---|
| `df_proj_dir` | 工程根 | 重要!!，禁止丢弃 |
| `df_us_id` | 本次变更编号 | 重要!!，禁止丢弃 |
| `df_spec_dir` | `{df_proj_dir}/codespec/specs`，基线所在 | - |
| `df_change_dir` | `{df_proj_dir}/codespec/changes/{df_us_id}`，delta 落点 | - |

变量缺失时先跑一次 `df-env` 补齐。

## 步骤

### 1. 读基线

读基线 spec 一侧——可能是单文件 `{df_spec_dir}/spec.md`，也可能是按能力拆开的 `{df_spec_dir}/<capability>/spec.md`（多份都要读）。

- **一份都没有 → 停手**：没有基线就没有差异可言，让用户先建基线；本 skill 不代建。
- 存在 → 把每条 `### Requirement:` 的标题与它规定的行为记下来，后面所有判断都对着它做
- 顺带读 `{df_change_dir}/proposal.md`（若存在）：本次的需求草案、范围与关键取舍都在那里，差异要对着它写，别自己重造需求
- 同时读 `{df_proj_dir}/docs/arch.md` 与 `{df_proj_dir}/README.md`：架构现状与项目对外描述决定了哪些需求是「已有能力的延伸」、哪些是「新增能力」，差异必须与它们对齐

### 2. 读已有 delta

`{df_change_dir}/delta-spec.md` 若已存在，先读进来。本次是**更新**而不是覆盖：保住已经定稿的条目，只改需要改的部分。

### 3. 按 df-grill 盘问（冲突优先）

使用 `df-grill` 的方法盘问——设计树、一轮问完前沿、每轮给推荐、事实自己查、只走 AskUserQuestion。

**着力点是本次与基线的冲突**，不是基线本身。基线写了什么，你自己读，不问用户。每条问题都要能写成：

```
基线里 "### Requirement: <名字>" 规定的是 X（spec.md:行号），本次要变成 Y，冲突在 Z，你选哪边？
```

要问出来的四件事：

| 方向 | 落点 | 要问出什么 |
|---|---|---|
| 归属哪条需求 | `## MODIFIED` / `## REMOVED` 的条目名 | 动的是基线里哪一条，还是全新能力 |
| 差异性质 | 落进哪一节 | 新增 / 修改 / 删除 / 改名，四类互斥 |
| 验收行为 | `#### Scenario:` | 改后的 WHEN/THEN，必须是可观测的 |
| 兼容性影响 | `## Impact` | 旧行为留不留、谁会受影响 |

不许问：基线里某条需求是干什么的、为什么不这么写、要不要顺手重构——没有冲突就不问。

### 4. 写或更新 delta-spec.md

按 `templates/delta-spec.md` 填，落盘到 `{df_change_dir}/delta-spec.md`：

- 四个差异小节（`ADDED` / `MODIFIED` / `REMOVED` / `RENAMED`）**用哪些留哪些**，空的一节整节删掉，不留空标题
- 本次确实没有需求差异时（纯重构、纯技术债），**不要编需求**：四节全删，改写成 `## Skipped` + 一句理由，这就是合法产出
- 每条需求写成 `### Requirement: <名字>`，正文用 `SHALL` 陈述
- **每条需求至少一个 `#### Scenario:`**，固定 `- **WHEN** ...` / `- **THEN** ...`
- `MODIFIED` / `REMOVED` 必须点明基线里的对应条目名，否则读者无法对照
- 基线按能力拆成多份时，条目名写成 `<capability>/<需求名>`，例如 `order-export/按条件导出订单`；单文件布局直接写需求名即可
- `## Impact` 写清与基线的冲突与兼容性取舍
- 模板里的 `<...>` 与 HTML 注释全部替换，不留一处

### 5. 回读校验

- 合法产出只有两种：至少一节差异小节非空，**或** `## Skipped` 存在且四节为空
- 四节全空又没写 `## Skipped` 才算不合格——那说明本次没有差异却仍被要求产出文件
- 每条 `### Requirement:` 后至少一个 `#### Scenario:`
- `MODIFIED` / `REMOVED` 里的条目名能在基线 `spec.md` 中找到
- 无 `<...>`、`<!-- -->`、`TODO` 残留；frontmatter `status` 改成 `done`

### 6. 简报与确认

收尾前写一段简报（不超过 8 行），直接放进下面提问卡的 `question`，不要另起一段。简报至少包含：

- 落盘路径：`delta-spec.md`
- 四类差异各几条（ADDED / MODIFIED / REMOVED / RENAMED）
- 动了基线的哪几条需求，兼容性怎么取舍
- 仍然存在的假设（没有就写"无"）

```js
AskUserQuestion({
  "questions": [
    {
      "header": "验收（要改什么就直接输入）",
      "question": "【简报：结论 / 证据 / 风险，不超过 8 行】\n\n符合你的要求吗？不符合就直接输入要改的地方。",
      "options": [
        {"label": "符合", "description": "delta-spec 定稿"}
      ],
      "multiSelect": false
    }
  ]
})
```

- 只有两类回答：`符合`，或用户直接输入修改意见
- 用户输入 → 按意见改 → 重新出简报 → 再问一次
- **迭代上限 3 轮**；到顶仍未确认，列出未达成项并停手，不再自行修改

## 边界

- **只写 `{df_change_dir}/delta-spec.md`**：不写 `spec.md`、`design.md`、`delta-design.md`、`task.md`、`validation.md`。
- **不改基线**：基线要变，属于基线创建与补正那一步的职责。
- **不改代码**，**不推进 `df_stage`**。
- **提问只用 AskUserQuestion**，方向受第 3 步表格约束。
- **宿主没有 AskUserQuestion 时**：退回编号列表提问，不跳过提问。
