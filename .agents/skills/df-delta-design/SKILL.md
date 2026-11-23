---
name: df-delta-design
description: 针对一条 US 变更，读取基线 design.md 与该变更的 delta-spec.md，盘问设计冲突，创建或更新该变更的 delta-design.md。
---

df-delta-design 产出一份东西：`{df_change_dir}/delta-design.md`——本次变更的设计方案与对基线架构的影响。不改代码，不改基线。

## 变量

| 变量 | 用途 | 说明 |
|---|---|---|
| `df_proj_dir` | 工程根 | 重要!!，禁止丢弃 |
| `df_us_id` | 本次变更编号 | 重要!!，禁止丢弃 |
| `df_spec_dir` | `{df_proj_dir}/codespec/specs`，基线所在 | - |
| `df_change_dir` | `{df_proj_dir}/codespec/changes/{df_us_id}`，delta 落点 | - |

变量缺失时先跑一次 `df-env` 补齐。

## 步骤

### 1. 读三份输入

按顺序读，缺任何一份都要停手：

| 文件 | 缺失时的处理 |
|---|---|
| `{df_change_dir}/delta-spec.md` | **停手**：没有需求差异就没法设计差异，先补齐它 |
| `{df_change_dir}/proposal.md` | 可跳过（仅提示）：背景、范围与取舍在这里，设计取舍要与它一致 |
| `{df_proj_dir}/docs/arch.md` | 架构现状；设计不能与既有分层和依赖方向冲突 | **停手**：没有架构现状就无法判断冲突 |
| `{df_proj_dir}/README.md` | 项目对外描述；改动若影响使用方式要在这里体现 | 可跳过（仅提示） |
| 基线 spec（`specs/spec.md` 或 `specs/<capability>/spec.md`） | **停手**：一份都没有说明工程还没建基线 |
| `{df_spec_dir}/design.md` | **停手**：同上 |

三份都在，再读 `{df_change_dir}/delta-design.md`（若已存在，本次是更新而不是覆盖）。

### 2. 定位冲突

先把这三类事实自己找出来，别拿去问用户：

- `delta-spec.md` 的每条需求，落在基线的哪些组件上（对着 `design.md` 的「组件与依赖」「架构总览」）
- 本次是否破坏既有依赖方向，是否与 `docs/adr/` 里已记录的决策冲突
- 是否有公共接口、数据所有权、部署形态要动

### 3. 按 df-grill 盘问（冲突优先）

使用 `df-grill` 的方法盘问，只走 AskUserQuestion。每条问题都要能写成：

```
基线 design.md 里 <章节/组件> 是 X（design.md:行号），本次要变成 Y，冲突在 Z，你选哪边？
```

要问出来的四件事：

| 方向 | 落点 | 要问出什么 |
|---|---|---|
| 改动落点 | `## Changes` 表格 | 哪个模块改什么，一条需求对一行 |
| 结构影响 | `## Changes` 的备注 | 只写"哪个组件增删、依赖方向怎么变"一句话，图不在本文件 |
| 基线与回滚 | `## Baseline Diff`、`## Risks / Rollback` | 实现后基线哪几节要变；失败怎么退 |

不许问：基线某个组件是干什么的、代码怎么组织的、要不要顺手重构——没有冲突就不问。

### 4. 写或更新 delta-design.md

按 `templates/delta-design.md` 填，落盘到 `{df_change_dir}/delta-design.md`：

- `## Scope` 按需求名对齐 `delta-spec.md`，不重述需求正文；`delta-spec.md` 声明了 `## Skipped` 时，这里写明"本次不涉及需求变更"
- **不画图**：架构、组件依赖与流程时序成文在 `{df_change_dir}/delta-arch.md`；这里只列改动与基线差异
- **先过 `df-simple` 的删除拷问**：每个新增的类/结构体/函数/字段，先能回答「不加会破坏哪条验收判据」，答不上来就不写进 `## Changes`
- `## Changes` 表格每行对应一条需求，路径写真实模块路径
- `## Baseline Diff` 是合并基线的唯一依据，必须写清哪几节、变成什么

若本次命中结构性修改判据——新增或删除模块/服务、依赖方向反转、换技术栈或部署形态、公共接口或数据所有权跨模块转移、目录分层重排——`## Baseline Diff` 必须逐条覆盖，一处含糊都会让合并后的基线失真；同时要求 `{df_change_dir}/delta-arch.md` 在图里体现这些结构变化。
- `## Assumptions` 只在真有假设时保留，否则整节删掉
- 模板里的 `<...>` 与 HTML 注释全部替换

### 5. 回读校验

- 五节齐全：`Context` / `Scope` / `Changes` / `Baseline Diff` / `Risks / Rollback`
- `## Changes` 覆盖 `delta-spec.md` 里的每一条需求，一条不漏
- 全文不含 ```mermaid 围栏（图不属于本文件）；若残留，删掉并确认信息已在 `{df_change_dir}/delta-arch.md` 里
- 无 `<...>`、`<!-- -->`、`TODO` 残留；frontmatter `status` 改成 `done`

### 6. 简报与确认

收尾前写一段简报（不超过 8 行），直接放进下面提问卡的 `question`，不要另起一段。简报至少包含：

- 落盘路径：`delta-design.md`
- 受影响组件数；`## Changes` 覆盖了 delta-spec 的哪几条需求
- 流程是否涉及跨组件调用；`## Baseline Diff` 涉及基线哪几节
- 仍然存在的假设（没有就写"无"）

```js
AskUserQuestion({
  "questions": [
    {
      "header": "验收（要改什么就直接输入）",
      "question": "【简报：结论 / 证据 / 风险，不超过 8 行】\n\n符合你的要求吗？不符合就直接输入要改的地方。",
      "options": [
        {"label": "符合", "description": "delta-design 定稿"}
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

- **只写 `{df_change_dir}/delta-design.md`**：不写 `spec.md`、`design.md`、`delta-spec.md`、`task.md`、`validation.md`。
- **不改基线**：基线要变属于创建与补正那一步；本 skill 只在 `## Baseline Diff` 里预告怎么变。
- **不改代码**，**不推进 `df_stage`**。
- **提问只用 AskUserQuestion**，方向受第 3 步表格约束。
- **宿主没有 AskUserQuestion 时**：退回编号列表提问，不跳过提问。
