---
status: done
---

# Review

## 评审包

| 项目 | 内容 |
|---|---|
| 变更范围 | 两套主题调色板/QSS、按钮四 variant、方形勾选与单选、标签、输入、提醒、字体 |
| 对应需求 | 主题视觉规范、主题字体、卡片描边 |
| 验证证据 | 217 passed；verify light/dark 退出 0；font_probe 显示 app 与组件字体均为 HarmonyOS Sans SC；截图对比参考图 |
| 边界比对 | 只改 theme、画廊文案、两条测试与文档 |

## 意见清单

| ID | 档位 | 位置 | 问题 | 证据 | 结论 |
|---|---|---|---|---|---|
| R1 | 严重 | theme 构建 | 运行中的 obox 锁 pyd，构建失败；已改为构建前关闭实例 | build 输出文件占用 | 接受 |
| R2 | 一般 | button.py | modal 仍用 primary= 构造；已保留兼容参数 | e2e TypeError | 接受 |
| R3 | 一般 | input.py | 文本域仍引用 LINE；已统一 INPUT_BORDER | NameError | 接受 |
| R4 | 一般 | 测试 | 提醒色/控件高度断言过期；已更新断言 | 测试失败 | 接受 |

## 回归

- uv run pytest -q → 217 passed
- verify_ui light/dark → 退出 0
- font_probe → app font 与组件 font 均为 HarmonyOS Sans SC
- check.py 变更与基线 → 0

## 结论

- 严重：剩余 0
- 一般：0
