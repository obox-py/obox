---
status: done
---

# Tasks

| ID | 任务 | 方式 | 涉及文件 | 需求 | 依赖 | 完成判据 | 状态 |
|---|---|---|---|---|---|---|---|
| T1 | 单实例管道 | 主 Agent | obox/ui/single_instance.py、obox/app.py、tests/test_single_instance.py | 单实例运行 | - | 第二个实例发出 show 后退出；不同用户名管道不同 | 完成 |
| T2 | 托盘常驻 | 主 Agent | obox/ui/tray.py、obox/app.py | 托盘常驻 | T1 | 托盘图标出现，菜单三项可用，双击恢复 | 完成 |
| T3 | 关闭行为与对话框 | 主 Agent | obox/ui/close_dialog.py、obox/ui/main_window.py、obox/app.py、tests/test_close_action.py | 关闭行为 | T2 | 三选一生效，记住选择写配置，直接模式不弹窗 | 完成 |
| T4 | 设置「行为」分类 | 主 Agent | obox/app.py、tests/test_settings_close.py | 关闭行为设置 | T3 | 设置页出现行为分类与三项，切换即时生效 | 完成 |
| T5 | 验证与文档合并 | 主 Agent | scripts/verify_ui.py、README、docs、codespec | 全部 | T4 | verify 通过；check 变更与基线 0 | 完成 |

## 任务详情

- T1：单测直接构造 SingleInstance，先 listen 再 try_notify
- T2：启动应用检查 QSystemTrayIcon.isSystemTrayAvailable 分支
- T3：decide_close 纯函数用例覆盖 ask/tray/quit 与 remember
- T4：设置数据里断言 behavior 组与 close_action 项
- T5：verify_ui 增加托盘/关闭场景（无法点击托盘时至少断言托盘对象存在）

## 测试策略

单实例与关闭决策走单测；托盘与对话框走应用级断言；设置走 _settings_groups 数据断言。

## 自检

- [x] 需求都有任务
- [x] 依赖无环
- [x] 判据可执行

## 执行顺序

T1 → T2 → T3 → T4 → T5