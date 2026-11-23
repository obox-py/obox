---
name: df-arch
description: 针对一条 US 变更做增量架构分析——只分析待改模块与它们的直接关联模块，产出 delta-arch.md（含时序图与 UML 图），不做全量架构盘点。
---

df-arch 只回答一个问题：**这次改动会把架构动成什么样**。它产出 `{df_change_dir}/delta-arch.md`，不做全量盘点、不维护项目级 `docs/arch.md` 与 `README.md`（那些在基线阶段维护）。

## 变量

| 变量 | 用途 | 说明 |
|---|---|---|
| `df_proj_dir` | 工程根 | 重要!!，禁止丢弃 |
| `df_us_id` | 本次变更编号 | 重要!!，禁止丢弃 |
| `df_change_dir` | `{df_proj_dir}/codespec/changes/{df_us_id}`，delta-arch.md 落点 | - |

变量缺失时先跑一次 `df-env` 补齐。

## 模板

| 产物 | 模板 |
|---|---|
| `{df_change_dir}/delta-arch.md` | `templates/delta-arch_template.md` |

模板里的 `{{...}}` 与 HTML 注释全部替换，落盘前清零。

## 步骤

### 1. 读输入

| 文件 | 用途 | 缺失时 |
|---|---|---|
| `{df_change_dir}/delta-design.md` | 改动清单与 `## Baseline Diff`，决定要分析哪些模块 | **停手**：缺它就没有改动范围 |
| `{df_change_dir}/delta-spec.md` | 需求口径，判断调用链边界 | **停手** |
| `{df_change_dir}/proposal.md` | 背景与「不做」清单，防止分析越界 | 可跳过 |
| `{df_proj_dir}/README.md` | 项目对外描述，判断改动是否影响使用方式 | 可跳过 |
| `{df_proj_dir}/docs/arch.md` | 全局架构，作为对照基线 | 可跳过，但要提示用户「全局架构文档尚未建立」 |

### 2. 圈定分析范围（只扩大一跳）

从 `delta-design.md` 的 `## Changes` 与 `## Baseline Diff` 出发：

1. 列出**待修改模块**——本次真正要改的
2. 列出它们的**直接关联模块**——只算一跳：直接调用它、被它调用、与它共享数据契约的
3. **不扩到二跳**。二跳及以上只在 `## 对整体架构的影响` 里用一句话带过

范围要能对上 `scope.md` 的白名单：白名单外的模块，只作为「明确不动」的对照出现在关联表里。

### 3. 读代码拿事实

对圈定的每个模块，读真实文件确认：模块路径、对外接口签名、依赖方向、现有调用链。**表格里的每一行都要能在代码里找到出处**，不许凭 `design.md` 的措辞推测。

### 4. 与用户确认影响面

分析结果先讲一遍，只问真正需要用户定的（提问只用 AskUserQuestion）：

```js
AskUserQuestion({
  "questions": [
    {
      "header": "影响面（也可直接输入要补的模块）",
      "question": "本次要改 <模块 A、B>，直接关联 <C、D>，其中 <C> 是否也要动？",
      "options": [
        {"label": "C 不动", "description": "只作为关联模块出现，接口保持不变"},
        {"label": "C 要动", "description": "我会把它列入待修改模块，并补进 scope 讨论"},
        {"label": "关联模块我另指", "description": "你直接给模块路径，我按你给的圈定"}
      ],
      "multiSelect": false
    }
  ]
})
```

### 5. 加载 df-simple（写之前）

先加载 `df-simple` skill，按它的设计期规则把本次要引入的流程、模块与接口逐个问一遍，再进第 6 步。

### 6. 写 delta-arch.md

按模板填，落盘到 `{df_change_dir}/delta-arch.md`：

- **时序图与 UML 图是必需的**：时序图画本次改动涉及的关键调用链，UML 用类图或组件图说明改动后的结构关系
- 其他视图（上下文图、部署图、数据模型）**只在本次确实牵动时才画**，否则整节删掉
- 参与者与节点必须是 `## 待修改模块` 或 `## 直接关联模块` 里出现过的，不许画没读过的组件
- `## 对整体架构的影响` 要明确回答：有没有改变既有分层、依赖方向、部署形态；没有就写「无结构性影响」
- frontmatter `status` 改成 `done`

### 7. 回读校验

- 模板要求的必备小节齐全；`{{...}}` 与注释清零
- 至少一张 `sequenceDiagram` 与一张 `classDiagram`（或组件 `flowchart`），围栏闭合
- 抽查图里 3 个节点名，必须能在实读文件中找到
- 待修改模块与 `scope.md` 白名单不矛盾（白名单外的模块不许出现在「待修改」表里）
- 第 5 步确实执行过：能点出被删掉或保留下来的构件，且对得上用户的验收判据

### 8. 简报与确认

简报（不超过 8 行）写进下面提问卡的 `question`：待改模块几个、直接关联几个、接口有无变化、两张图分别画了什么、对整体架构的结论、范围外但值得注意的风险。然后提一题：

```js
AskUserQuestion({
  "questions": [
    {
      "header": "验收（要改什么就直接输入）",
      "question": "【简报：结论 / 证据 / 风险，不超过 8 行】\n\n这份增量架构分析符合你的要求吗？不符合就直接输入要改的地方。",
      "options": [
        {"label": "符合", "description": "delta-arch.md 定稿"}
      ],
      "multiSelect": false
    }
  ]
})
```

- 只有两类回答：`符合`，或用户直接输入修改意见
- 用户输入 → 按意见改 → 重新出简报 → 再问一次
- **迭代上限 3 轮**；到顶列出未达成项并停手

## 边界

- **只写 `{df_change_dir}/delta-arch.md`**：不写 `docs/arch.md`、`README.md`（项目级文档归基线阶段维护）、不写 spec/design/delta/task/scope/validation/review。
- **只做增量**：不盘点全量模块、不重画系统上下文图、不写与本次无关的架构说明。
- **范围只扩大一跳**：二跳以上只在「对整体架构的影响」里一句话带过。
- **不改代码**，**不推进 `df_stage`**。
- **图不许凭空造**：节点与依赖方向必须有代码出处。
- **提问只用 AskUserQuestion**。
- **宿主没有 AskUserQuestion 时**：退回编号列表提问，不跳过提问。
