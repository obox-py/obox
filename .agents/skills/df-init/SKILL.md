---
name: df-init
description: dev-flow 的编排入口。进场必调 df-env 取工程、US 编号与阶段推断，逐阶段验收（每阶段一张卡、跳过要过闸、跳转要授权），收尾把四份 delta 分析后并入 spec/design/arch/README 再归档。
---

df-init 是唯一**持有并推进 `df_stage`** 的地方，其余 skill 只读。它自己不产出规格、设计、任务或代码——只决定"下一步该谁做"，并在每一阶段验收通过后把状态推进一格。

## 变量

| 变量 | 来源 | 说明 |
|---|---|---|
| `df_proj_dir` | `df-env` | 重要!!，禁止丢弃 |
| `df_us_id` | `df-env` | 重要!!，禁止丢弃 |
| `df_change_dir` | 派生 | `{df_proj_dir}/codespec/changes/{df_us_id}` |
| `df_spec_dir` | 派生 | `{df_proj_dir}/codespec/specs` |
| `df_stage` | 本 skill 推断与推进 | 不落文件，每次进场重建 |

`df_stage` 的取值与顺序：

```
env --> proposal --> delta-spec --> delta-design --> arch --> task --> scope --> validation --> solver --> review --> done
```

## 步骤

### 0. 加载输出纪律（df-cheap-talk）

进场第一件事：按 `df-cheap-talk` 的篇幅预算约束本轮所有输出。它只管表达，不改流程。

- 阶段简报 ≤ 8 行；总汇 ≤ 12 行；提问卡 1 题、选项 ≤ 4 个
- 先给结论再给理由；不写总结章、不写追问菜单、不复述问题
- 证据（命令输出、路径、失败原因）与风险不在压缩范围内
### 1. 定位（调用 df-env）

**进场必调 `df-env`**：它负责定工程、建骨架、定 US 编号，并推断每条变更的阶段。变量已存在时它跳过定位提问，但阶段推断照做。

拿回：`df_proj_dir` / `df_us_id` / `df_change_dir` / `df_spec_dir` + 阶段推断结果。

### 2. 取阶段（向 df-env）

**本 skill 不再扫 @@changes/@@，也不再自己推断**——阶段推断是 @@df-env@@ 的职责，全流程只有那一份实现。

- 第 1 步的 @@df-env@@ 调用已经返回了每条变更的 @@df_stage@@，这里直接用它的结果
- @@df-env@@ 的返回值：四个变量 + 当前 @@df_us_id@@ 对应变更的阶段 + 全部在飞变更的阶段表
- 结果与磁盘不一致时以 @@df-env@@ 为准，并把差异在简报里说一句，**不许在这里重算**

判据（由 @@df-env@@ 执行）：**产物在、且自报 @@status: done@@**。本 skill 只消费结论。

### 3. 总览与选择

把 `df-env` 返回的阶段表原样列出（编号 / 功能名 / 当前阶段 / 完成度），不重新推断。然后提一题：

```js
AskUserQuestion({
  "questions": [
    {
      "header": "从哪条开始（也可直接输入 US 编号）",
      "question": "下面是在飞的变更，选一条继续，或新建一条。",
      "options": [
        {"label": "<US 编号 1> - <功能名>", "description": "当前阶段：<df_stage>，剩余：<还剩几步>"},
        {"label": "<US 编号 2> - <功能名>", "description": "当前阶段：<df_stage>，剩余：<还剩几步>"},
        {"label": "新建一条", "description": "交给 df-env 定工程与编号，从 env 阶段开始"}
      ],
      "multiSelect": false
    }
  ]
})
```

**这一题不许省略**：在飞变更只有一条时也要问，不许因为"只剩一条"就直接进入该阶段；用户没明确选中某条之前，不许调用任何阶段 skill。

### 4. 逐阶段驱动

从 `df_stage` 指向的阶段开始，按顺序调用对应 skill：

| 阶段 | 调用的 skill | 进入条件 |
|---|---|---|
| `proposal` | `df-proposal` | 基线缺失，**或 `proposal.md` 缺失/未 done** |
| `delta-spec` | `df-delta-spec` | 基线已 `done` |
| `delta-design` | `df-delta-design` | `delta-spec.md` 已 `done` |
| `arch` | `df-arch` | `delta-design.md` 已 `done` |
| `task` | `df-task` | `{df_change_dir}/delta-arch.md` 已生成 |
| `scope` | `df-scope` | `task.md` 已 `done` |
| `validation` | `df-validation` | `scope.md` 已 `done` |
| `solver` | `df-solver` | `validation.md` 已 `done` |
| `review` | `df-review` | 每次都跑，不看 `done`，也不设跳过闸门 |

推进规则：

- **每阶段单独验收**：一个阶段一张提问卡、一次确认，卡片里带该阶段的简报；用户点`符合`之后，`df-init` 才把 `df_stage` 推进到下一格
- 不合并验收关：`delta-spec` 与 `delta-design` 是两张卡，`arch`、`task`、`scope` 也各是一张卡
- 用户输入修改意见 → 交回该阶段迭代，`df_stage` 保持不动
- 阶段产物已 `done` → **不等于可以跳过**：必须过下面的跳过闸门（盘问冲突与差异 → 裁决 → 更新 → 确认）
- **跳转要授权**：换目标阶段走下面的「跳转」规则，不许自己改道
- `proposal` 阶段有两条路：基线缺失就建基线（写 `spec.md` / `design.md`），基线齐备就只盘问、只写 `proposal.md`——**两种情况都要有 `proposal.md`**
- **不许静默跳阶段**；`validation` 也不许因为「看起来没必要」就省——要省就走闸门，用户点头才算
- 任一阶段报错或阻塞 → 停下并报告卡在哪，不擅自换路

#### 跳过闸门（逐阶段）

`df_stage` 指向的阶段已有 `status: done` 的产物，或判断某个阶段可以省掉时，不许直接进下一格，按三步过闸。没有独立产物的阶段以它的完成判据为准，例如 solver 看 `task.md` 是否全部完成。`review` 不设闸门，每次都跑。

1. **盘问冲突与差异**：加载 `df-grill`，把「本次变更 vs 该阶段已有产物」的冲突（两边互相矛盾）与差异（内容对不上本次需求）逐条列出；每条写清现象、影响与**处理建议**；彼此没有因果关系的合成一次提问（多题并列），有因果的分轮问
2. **裁决与更新**：按用户的裁决改该产物，改完仍保持 `status: done`；裁决为「不改」就不动文件
3. **确认跳过**：另出一张提问卡「这个阶段可以跳过吗」，卡里带第 1 步的冲突/差异结论；同意才进下一格，不同意就正常调用该阶段的 skill

- **跳过只作用于当前阶段**：同意跳过 `delta-spec`，不等于 `delta-design` 也能跳，后者仍要自己过闸
- 闸门**逐阶段一问**，不和其他阶段合并
- 任务简单时同样要过闸：先列出要跳的阶段与理由，用户同意后才跳
- 空口「已核对」不算证据；给不出冲突/差异结论就按没跳过处理

#### 跳转（需授权）

默认按阶段表的顺序推进。当某阶段的结果暴露出上游缺口（如 `df-review` 发现需求口径漏了），或确认某些阶段可以省时，`df-init` 可以提议跳到任意阶段——前跳或回退都行。

- 提议卡必须写三件事：**目标阶段**、**理由**（哪个结果暴露了什么）、**影响**（哪些产物要重做或复核）
- 用户同意才跳；拒绝就按正常顺序推进，不擅自改道
- 跳转不改跳过规则：落到目标阶段后，产物已 `done` 仍要过闸门

### 5. 收尾汇报

`df_stage` 到 `done` 时输出一份总汇（不超过 8 行）：

- 本次变更：`{df_us_id}` 与其功能名
- 产物的路径与最终状态（proposal / spec 侧 / design.md / delta-spec / delta-design / arch / task / scope / validation / review）
- 任务完成情况：`完成/总数`，阻塞项点名
- 评审结论：`review.md` 的分档分布与"严重剩余 0"
- 合并结果：spec / design / arch / README 四份各自「已合并 / 未合并」
- 遗留项（来自 `validation.md`）

这一步不再问验收——每个阶段已经问过了，重复提问只会让用户厌烦。若用户要改，回第 4 步重进对应阶段。

汇报之前先把**四份 delta 合并进项目级文档**——不合并就归档，这次的需求、设计与结构分析都会随 change 目录一起被埋起来。

**禁止用脚本做字符串追加**。合并是判断活：先读懂 delta 想表达什么，再决定基线里哪一节改写、哪一节新增、哪一节保留。脚本只会追加，会把过时描述留在文档里。

| 从 | 并入 | 怎么合并 |
|---|---|---|
| `{df_change_dir}/delta-spec.md` | `{df_spec_dir}/spec.md`（或对应 capability 那份） | ADDED 新增 Requirement；MODIFIED 用新内容替换同名 Requirement 整节；REMOVED 删节；RENAMED 改标题并保留正文 |
| `{df_change_dir}/delta-design.md` | `{df_spec_dir}/design.md` | 决策按 `## Decisions` 逐条并入；被取代的旧决策删掉，不并列保留 |
| `{df_change_dir}/delta-arch.md` | `{df_proj_dir}/docs/arch.md` | 待改模块与依赖变化写进对应分层节；时序图与 UML 图替换过时那张，不新增重复图 |
| 以上三份的共同结论 | `{df_proj_dir}/README.md` | 只改受影响章节（能力清单、使用方式、目录结构），不重写用户自己写的段落 |

合并顺序固定：**spec → design → arch → README**。前一份合并完再读后一份，避免同一处被改两次。

合并完成后：

- 逐条回读被改写的章节，确认没有把 delta 的措辞原样搬进基线（基线写事实，不写「本次将……」）
- 跑 `python <df-validation 目录>/scripts/check.py --proj {df_proj_dir} --us {df_us_id} --baseline-only`，基线结构项必须全绿
- 三份 delta 保留在 change 目录里作为历史，不删除
- 任一失败就停下报告，**不要带着未合并的产物归档**

汇报之后提一问，只关于归档：

```js
AskUserQuestion({
  "questions": [
    {
      "header": "归档（也可直接输入保留理由）",
      "question": "这条变更已完成，是否归档？归档后它不再出现在在飞列表里，磁盘上仍保留在 changes/archive/ 下。",
      "options": [
        {"label": "归档 (Recommended)", "description": "changes/<US> 移到 changes/archive/<US>，六份产物原样保留"},
        {"label": "暂不归档", "description": "继续留在在飞列表，之后可再归档"}
      ],
      "multiSelect": false
    }
  ]
})
```

归档用脚本，不手搬目录：

```bash
python "<本 skill 目录>/scripts/archive_change.py" --proj "{df_proj_dir}" --us "{df_us_id}"
```

- 退出码 0 才算归档成功；目标已存在或源目录不在都返回非 0 并说明原因
- 归档不是删除：产物一份不少，只是离开 `changes/US-*` 扫描面
- 归档后不再对这条变更调用任何阶段 skill；要改就开新 US

## 边界

- **编排为主，唯一例外是收尾合并**：阶段产物一概不写；只有收尾把四份 delta 分析后并入四份项目级文档。
- **只有本 skill 推进 `df_stage`**：其他 skill 只读，不许自行推进。
- **不落盘 `df_stage`**：每步都从磁盘重建，不靠记忆也不写状态文件。
- **不许静默跳阶段**：跳过必须过闸门——盘问冲突与差异、按裁决更新、用户确认；跳过与跳转都只作用于一个阶段，阶段之间仍有产物依赖，不许并行。
- **一阶段一验收**：不同阶段不复用同一张卡；跳转或跳过之后，从目标阶段重新出卡。
- **归档只移动目录**：不删产物、不改 status，也不动已合并的基线。
- **评审后基线必须再一致**：`df-review` 若有触及需求/结构的代码改动，先让上游更新 delta，再让 `df-solver` 重跑合并。
- **合并归本 skill，且必须分析后写入**：`df-solver` 只回填不写基线；spec / design / arch / README 的合并在收尾一次做完，禁脚本追加。
- **提问只用 AskUserQuestion**。
- **表达受 `df-cheap-talk` 约束**：本 skill 的输出是整条流程的样板，简报与提问卡超行数即不合格。
- **宿主没有 AskUserQuestion 时**：退回编号列表提问，不跳过提问。