---
status: done
---

# Review

## 评审包

| 项目 | 内容 |
|---|---|
| 变更范围 | 模板引擎（expr/template/builder）、视图数据与生命周期、应用清单与元数据、App 系统扩展、应用窗口与持久化、Image 组件 |
| 对应需求 | 模板指令与值绑定、视图数据与局部更新、视图生命周期、应用注册、应用页作为系统扩展、应用网格、打开应用与窗口复用 |
| 验证证据 | 189 passed；verify light 退出 0，新增「应用网格由 o-for 渲染」「点击卡片打开应用窗口」「应用窗口渲染扩展 UI」断言；截图 12_apps 与 13_app_window |
| 边界比对 | 全部落在白名单（obox、theme、extensions、tests、scripts、docs、README） |

## 意见清单

| ID | 档位 | 位置 | 问题 | 证据 | 结论 |
|---|---|---|---|---|---|
| R1 | 严重 | theme/*/components/image.py | build_widget 里调用 _load 时 self.widget 还没赋值，装配应用页直接崩 | 首次 verify 栈顶 ImageComponent._load AttributeError | 接受 |
| R2 | 严重 | obox/ui/builder.py | 绑定与区域的作用域把数据也拷了进去，set_data 后仍求值旧值 | 单测里 label 从旧改新不生效 | 接受 |
| R3 | 一般 | obox/i18n.py | id 规则不允许下划线，apps.no_ui 被整份 i18n.json 拒绝 | 启动日志提示 apps.no_ui 非法 | 接受 |
| R4 | 一般 | obox/app.py | 应用视图注入数据抛异常时连累后续视图挂载 | 首轮只有 app.main 挂上，demo/gallery 全没挂 | 接受 |

## 回归

- `uv run pytest -q` → 189 passed（新增 expr 3 例、template 4 例、manifest apps 5 例）
- `uv run python scripts/verify_ui.py` → 退出码 0，截图 12_apps 与 13_app_window
- `uv run python scripts/verify_ui.py --theme dark` → 退出码 0
- `uv run ruff check` → All checks passed

| R5 | 一般 | scripts/verify_ui.py | 用 set_text 清空搜索框不触发 input 事件，验证误判恢复失败 | verify 日志 FAIL 清空搜索恢复全部 | 接受：改用键盘清空 |
| R6 | 严重 | obox/app.py | 运行中新增/卸载扩展不会更新应用列表 | 需求明确要求同步 | 接受：文件监听 + 宿主重启 |

## 结论

- 严重：剩余 0（R1、R2 已修复）
- 一般：0（R3、R4 已修复）
