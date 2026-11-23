---
name: df-env
description: dev-flow 的定位与现状盘点阶段。确定本次改动落在哪个工程、建出 codespec 骨架、定出 US 编号，并扫 changes/US-* 推断各条变更所处的 df_stage。
---

df-env 做四件事：**定工程**、**建目录**、**定 US 编号**、**推断阶段**。不写任何产物文件。

## 变量

| 变量 | 值 | 说明 |
|---|---|---|
| `df_proj_dir` | 工程根，绝对路径，`/` 分隔 | 重要!!，禁止丢弃 |
| `df_us_id` | `US-{YYYYMMddHHmmss}-{4位序号}-{功能名}` | 重要!!，禁止丢弃 |
| `df_change_dir` | `{df_proj_dir}/codespec/changes/{df_us_id}` | - |
| `df_spec_dir` | `{df_proj_dir}/codespec/specs` | - |

## 变量从哪来（先解析，不足才问）

进场先解析，按优先级取第一个非空值，**取到就锁定，后续步骤不再提问**：

| 优先级 | 来源 | 判定方式 |
|---|---|---|
| 1 | **调用方入参** | `df-init` 等调用方必须把已知值传进来（`df_proj_dir=…`、`df_us_id=…`），收到即采用 |
| 2 | **会话内已定** | 本轮对话里已确认过的值 |
| 3 | **磁盘反推** | `codespec/changes/US-*` 存在时：`df_us_id` = 目录名，`df_proj_dir` = 该目录上溯三级 |

**已经有的变量绝不重问**。重问只应发生在某个变量确实无从得知时——尤其 `df_us_id`：用户或调用方一旦定下，不许再让用户选一次。

「必须先问」和「不许重问」不冲突：**首次定值要问，已定值不再问**。

## 阶段推断（本 skill 的第二个职责）

进场时扫 `{df_proj_dir}/codespec/changes/US-*`，对每条变更按磁盘现状推断 `df_stage`，随变量一起回传给调用方。**变量已存在时跳过定位提问，但推断照做。**

| 磁盘现状 | 推断阶段 |
|---|---|
| `{df_change_dir}` 不存在 | `env` |
| 基线 spec 一份都没有、或 `design.md` 缺失 | `proposal`（建基线形态） |
| 基线齐备，但 `proposal.md` 缺失或不是 `done` | `proposal`（仅盘问形态） |
| `delta-spec.md` 缺失或不是 `done` | `delta-spec` |
| `delta-design.md` 缺失或不是 `done` | `delta-design` |
| `{df_change_dir}/delta-arch.md` 不在，且 `docs/arch.md` 里也没有 `df-arch:{df_us_id}` 标记 | `arch` |
| `task.md` 缺失或不是 `done` | `task` |
| `scope.md` 缺失或不是 `done` | `scope` |
| `validation.md` 缺失或不是 `done` | `validation` |
| `task.md` 里仍有非`完成`的任务 | `solver` |
| `review.md` 缺失或不是 `done` | `review` |
| 以上全部满足 | `done` |

判据只有一条：**产物在、且自报 `status: done`**。扫描面只有 `changes/US-*`，已归档到 `changes/archive/` 的不参与推断。

推断结果随四个变量一起回传；**下游不重复扫描目录**——这是全流程唯一的阶段推断实现。
## 步骤

### 1. 定工程 df_proj_dir

**`df_proj_dir`已定义 → 跳过本步**，只校验目录还在。

抽线索：提示词里有显式路径且目录存在 → 直接进确认；否则先跑脚本拿全部候选目录的清单：

```bash
python "<本 skill 目录>/scripts/scan_projects.py" --root "{cwd}" --depth 4
```

输出一行紧凑 JSON，只有相对路径，**不打分**：

```json
{"root":"C:/projects/acme","dirs":["apps/admin","packages/order-service","packages/order-service/crates/ui","services/billing"],"truncated":false}
```

相关性由你判断：拿提示词里的模块名、技术栈词、路径片段去比 `dirs`，挑 2-4 个最相关的；都不相关、或提示词指向一个还不存在的位置时，再准备一个 `新建 - <推断的相对路径>`。候选、新建、当前工作目录合成同一题：

```js
AskUserQuestion({
  "questions": [
    {
      "header": "工程目录（可直接输入其他路径：绝对路径，或以 cwd 为基准的相对路径）",
      "question": "本次改动落在哪个目录？下面是我从 <N> 个工程目录里挑出的相关项。",
      "options": [
        {"label": "<相关候选 1>", "description": "df_proj_dir = <绝对路径>；依据：命中 <词>"},
        {"label": "<相关候选 2>", "description": "df_proj_dir = <绝对路径>；依据：命中 <词>"},
        {"label": "新建 - <推断的相对路径>", "description": "该位置还不存在，按这个位置新建一套"},
        {"label": "用当前工作目录", "description": "df_proj_dir = <cwd>"}
      ],
      "multiSelect": false
    }
  ]
})
```

用户直接输入路径时：`~` 展开、相对路径按 `{cwd}` 解析、`\\` 转 `/`、去尾斜杠，校验是目录，再把新路径填回这题重提。轮数上限 5，到顶只能选 `用当前工作目录`。

定案后当场写出值（绝对路径、`/` 分隔、无占位符）：

```
df_proj_dir = C:/projects/acme/packages/order-service
```

### 2. 建目录

一个脚本建齐 codespec 及其下的 specs、changes，幂等，不删任何已有内容：

```python
import os

base = r"{df_proj_dir}/codespec"
for d in (base, base + "/specs", base + "/changes"):
    os.makedirs(d, exist_ok=True)
```

跑完回读确认三个目录都在；失败就停在这里报错，不要带半套目录往下走。本步不设跳过：脚本幂等，跑一次比判断要不要跳过更省。

### 3. 定 US 编号 df_us_id

**`df_us_id` 已锁定（入参、会话或磁盘反推得到）→ 跳过本步**：不提问，只校验 `{df_proj_dir}/codespec/changes/{df_us_id}` 存在。

**只读目录名**：列 `{df_proj_dir}/codespec/changes/` 下的 `US-*` 目录（第 2 步已建好），不打开任何产物文件。

相关性：目录名末段的功能名与提示词各切 token（中文按连续汉字、英文按单词），**交集非空即相关**，按命中 token 数排序，取 **0-3 个**。你自己按提示词生成一个新的 US 编号作为新建项。

```js
AskUserQuestion({
  "questions": [
    {
      "header": "US 编号（直接输入功能名即可新建，规则：保留中文与字母数字，空格转 -，不超 20 字）",
      "question": "这条需求归到哪个 US？下面是我挑出的相关变更，或新建一条。",
      "options": [
        {"label": "<相关目录名 1>", "description": "匹配：<命中词>"},
        {"label": "<相关目录名 2>", "description": "匹配：<命中词>"},
        {"label": "新建 - <生成的完整编号>", "description": "按提示词里的功能名补齐时间戳与 4 位序号"}
      ],
      "multiSelect": false
    }
  ]
})
```

没有相关目录时，这题只剩 `新建 - <编号>` 一项。

**这一题必须等用户回答，不许自己往下走**：

- 候选只有一个、或者一个都没有，也要问——不许因为"显然只有这一条"就直接定 `df_us_id`
- 用户没回答（跳过、只回了个表情、回了别的内容）→ 重新问这一题，不许用"新建"或"最近修改的"兜底
- `df_us_id` 定下之前，不许创建 US 目录、不许写任何产物

选候选 → `df_us_id` 即该目录名，目录已存在，跳过下面的补建。选新建或直接输入功能名 → 该输入即功能名，按下面规则补齐编号，不再多问一题：

- 时间戳：当前本地时间 `YYYYMMddHHmmss`
- 序号：已有 `US-*` 中 4 位序号最大值 +1，零填 4 位；无历史则 `0001`
- 功能名：保留中文与字母数字，空格转 `-`，去 `\ / : * ? " < > |`，连续 `-` 合并，超过 20 字截断

选**新建**时，US 目录用脚本原子预留，不要手写 makedirs：

```bash
python "<本 skill 目录>/scripts/reserve_us.py" --proj "{df_proj_dir}" --name "<功能名>"
```

- 脚本用 `os.mkdir` 原子创建：目录已存在就换下一个序号重试，**两个进程同时预留不会拿到同一个编号**
- 输出 JSON：`us_id` / `path` / `index`；功能名按下面的规则 slug 化，时间戳取当前本地时间
- 选**已有候选**时不要跑它（目录已存在，直接采用 `df_us_id` = 目录名）
- 功能名与序号规则不变：时间戳 `YYYYmmddHHmmss`、序号零填 4 位、保留中文与字母数字、去 `\ / : * ? " < > |`、连续 `-` 合并、超 20 字截断

编号定下后当场写出三个值：

```
df_change_dir = {df_proj_dir}/codespec/changes/{df_us_id}
df_spec_dir   = {df_proj_dir}/codespec/specs/
```

## 边界

- **只建目录，不写产物**：不创建 `.md`、不填内容、不推进 `df_stage`（跑完仍是 `env`）。`spec.md`、`design.md`、`delta-spec.md`、`delta-design.md`、`task.md`、`validation.md` 全部由后续阶段创建与填充。
- **不落文件、不复述**：两个重要变量不写状态文件、不靠每步念叨；需要时从 `codespec/changes/US-*` 目录反推。
- **幂等**：重复跑不报错、不覆盖、不删除已存在的目录或文件。
- **并发边界**：骨架目录用 `makedirs(exist_ok=True)` 建，幂等，可并发；US 目录用 `reserve_us.py` 原子预留，不会撞号。
- **同一 US 不许两个会话同时推进**：本 skill 只保证编号不冲突；产物写入没有跨进程锁，同一个 US 并行跑后续阶段会互相覆盖。
- **候选只来自脚本**：相关性判断要在选项描述里写出依据（命中哪个词）；可以补 `新建`，但不能凭空编路径。
- **值不许凭记忆改写**：路径一律按目录反推的形态写，长路径不许截短。
- `df_change_dir` / `df_spec_dir` 永不单独提问，一律派生。
- 上层已有 `codespec/` 时只提示一行（父级另有规格，本次不与其共享），不改选。
- 路径展示给裸值，不加引号。
- **宿主没有 AskUserQuestion 时**：退回编号列表提问，不跳过提问。
