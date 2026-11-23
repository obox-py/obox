---
status: done
---

# Review

## 评审包

| 项目 | 内容 |
|---|---|
| 变更范围 | 新增 obox/ui/anchor.py 与 tests/test_anchor.py；改 obox/api/view.py、obox/app.py 与 obox-ext-dev 文档 |
| 对应需求 | 视图锚点与滚动（ADDED）；视图文件格式（MODIFIED） |
| 验证证据 | `pytest -q` → 269 passed；`verify_ui --theme light|dark` → 各 0 失败；`check_all.py` → 全通过 |

## 作者自查

- [x] 每个 `完成` 任务的验收命令都真的跑过，并有输出
- [x] `check.py` 无严重项
- [x] 变更没有超出 delta-spec 的范围
- [x] 没有把"看起来对"当成"验证过"

## 意见清单

| ID | 档位 | 位置 | 问题 | 证据 | 结论 |
|---|---|---|---|---|---|
| R1 | 一般 | 设置页 | 改版后偏紧凑，用户要求还原（处理：恢复左分类右条目，撤掉单页与吸顶，文档同步收窄） | 用户反馈与截图 | 接受 |
| R2 | 一般 | `obox/ui/anchor.py` | 锚点能力暂无产品内使用者，只有单测（处理：保留为通用能力，Impact 与遗留里写明） | 设置页已还原 | 接受 |
| R3 | 建议 | `obox/app.py` | 文件超过 1300 行（处理：登记长度表，不在本次拆分） | wc -l | 部分接受 |
| R4 | 建议 | `obox/ui/anchor.py` | sticky 只取第一个，多个被忽略（处理：写进 spec 与扩展文档） | 代码与文档 | 接受 |
| R5 | 建议 | `scripts/verify_ui.py` | verify 不覆盖锚点（处理：锚点用单测覆盖，设置页恢复原场景） | 测试清单 | 接受 |

## 长度超阈值

| 位置 | 行数 | 为什么不能再拆 |
|---|---|---|
| `obox/app.py` | 1330 | 装配中枢：视图挂载、锚点路由、扩展管理、托盘与关闭都在这里；拆出视图装配器牵动 6 个调用点，收益低于跨模块查找成本 |

## 回归

- R1：`uv run python scripts/verify_ui.py --theme light` 与 `--theme dark` → 各 0 失败；设置页恢复原分类切换，截图 15/16/19 重新生成
- 全量：`uv run pytest -q` → 269 passed；`check_all.py` → 全通过

## 结论

- 严重：剩余 0 条
- 一般：R1、R2 接受并已落到文档
- 建议：R3 部分接受（登记长度表）；R4、R5 接受
