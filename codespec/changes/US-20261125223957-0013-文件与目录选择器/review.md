---
status: done
---

# Review

## 评审包

| 项目 | 内容 |
|---|---|
| 变更范围 | 新增 obox/api/picker.py、obox/ui/picker.py、obox/ui/picker_remote.py；obox/app.py 路由；paramiko 依赖；tests/test_picker.py；verify 场景 27 |
| 对应需求 | 文件与目录选择器、远端文件浏览（ADDED）；依赖与安装包（ADDED） |
| 验证证据 | pytest 305 passed；verify light/dark 各 0 失败；真机 SSH 113.44.210.175 连接成功并列目录；check_all 通过 |

## 意见清单

| ID | 档位 | 位置 | 问题 | 证据 | 结论 |
|---|---|---|---|---|---|
| R1 | 一般 | obox/core/bus.py | 本地扩展的请求应答不会结束挂起请求（send 只分发不结算），picker 改用 bus.receive 投递应答规避（（core 不在本次范围）） | 真机/verify 超时 | 部分接受 |
| R2 | 一般 | obox/ui/picker.py | 窗口模态下 QTest.qWait 不投递线程信号，verify 曾超时（处理：verify 用 processEvents 循环；真实用户交互不受影响） | 复现脚本 | 接受 |
| R3 | 一般 | 选择器界面 | 首版工具栏只有新建文件夹，缺参考图的组织/视图切换与面包屑分段（（后续补）） | tmp/2.png 对比 | 部分接受 |
| R4 | 建议 | 图标 | 列表用 emoji 图标，未走主题图标（（可后续换 SVG）） | 截图 | 接受 |
| R5 | 建议 | 远端 | 只浏览与选择，不做上传/下载 | 需求范围 | 接受 |
| R6 | 建议 | 示例 | 未加 demo 扩展（处理：新增 extensions/pickerdemo，四按钮覆盖本地/远端×文件/目录，结果回填） | 任务 T7 | 接受 |

## 回归

- pytest 305 passed（含 4 条 picker 测试）
- verify light / dark 各 0 失败，新增 27_picker 截图与「返回路径」断言
- 真机 SSH：/ 与 /root 列举正常；指纹确认路径已走通

## 结论

- 严重：剩余 0 条
- 一般：R1、R3 部分接受；R2 接受
- 建议：R4、R5 接受；R6 部分接受