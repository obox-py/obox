---
status: done
---

# Validation

## 检查范围

| 文件 | 存在 | 本次结论 |
|---|---|---|
| `spec.md` | 是 | 无问题 |
| `design.md` | 是 | 无问题 |
| `delta-spec.md` | 是 | 1 处冲突（已有翻译通道缺口），已补条款 |
| `delta-design.md` | 是 | 1 处遗漏（宿主翻译通道未列改动落点），已补 |
| `delta-arch.md` | 是 | 1 处遗漏（缺 template/main_window 与 settings 模块），已补 |
| `task.md` | 是 | 2 处遗漏（settings 无任务、翻译通道无任务），已补 T13/T14 |
| `scope.md` | 是 | 与 task.md 不一致两处，已同步 |
| `proposal.md` | 是 | 无问题 |

## 问题清单

| ID | 档位 | 位置 | 问题 | 证据 | 处理 |
|---|---|---|---|---|---|
| V1 | 严重 | `task.md` 任务清单 / `scope.md` 明确不动 | 需求把 settings 扩进四语言覆盖，但没有任务，scope 还把 extensions/settings/** 列为不动 | delta-spec 的扩展清单含 settings；scope.md 原「明确不动」第 7 条；task.md 无 settings 任务 | 已修复 |
| V2 | 严重 | `delta-spec.md` 界面文案多语言覆盖 | 扩展的 Python/清单侧文案没有翻译通道：宿主只在装配 oml 前替换 i18n 占位符，视图数据、侧栏标题、showMessageBox、contributes.app.title 都原样输出 | obox/app.py:522 先 translate 再 assemble；obox/ui/template.py:14 注释「i18n 已在此之前替换」；main_window.py:318-319 tooltip 直接用 title | 已修复 |
| V3 | 一般 | `task.md` T2 | 「源码运行不可用」没有判定方式，core 又不能反向依赖 extensions 里的 _frozen() | obox/extensions/supervisor.py:15-20 | 已修复 |
| V4 | 一般 | `task.md` 全局约束 | 多个任务把中文搬进 i18n，但 scripts/verify_ui.py 对 zh-CN 原文有硬断言，任务没写「译文不得改 zh-CN 值」 | scripts/verify_ui.py:48-51、57、68、70、73 | 已修复 |
| V5 | 建议 | `task.md` T11 | verify_ui 只跑一次，没覆盖两套主题 | scripts/verify_ui.py:18 支持 --theme | 已修复 |
| V6 | 建议 | `task.md` / `delta-arch.md` | 文档里出现模板双花括号占位符，check.py 误判为未替换 | check.py 输出 E_TEMPLATE_BRACE | 已修复 |

## 处理记录

- 第 1 轮：check.py 报 12 项（严重 9 / 一般 3），其中 6 项是 task.md 覆盖检查表格列数与占位符写法导致的结构误报，4 项是 task.md/scope.md 的占位符残留，2 项是 validation.md 与 review.md 尚未生成。已修表格与措辞，结构项清零到只剩「validation.md 不存在」。
- 第 1 轮语义检查：发现 V1、V2 两条严重与 V3-V5 三条一般/建议。V2 交用户裁决，用户选「宿主侧补翻译通道」，据此同步改 delta-spec、delta-design、delta-arch、task.md（新增 T13/T14）与 scope.md 白名单。
- 第 2 轮：重跑 check.py，仅剩 validation.md 未生成与 review.md 未评审两项预期告警；语义复核未发现新增严重项。

## 遗留

- **已完成**：T5–T8 的扩展文案迁移；宿主在视图数据、组件状态修改、对话框与标题四处按扩展命名空间替换占位符。
- **已知缺口**：chartdemo 的 matplotlib 图内标题与月份名仍是中文（图在扩展进程里画成位图，宿主无法替换）；rdp 的 4 条内部 OSError 文案未迁移（开发者可见的异常文本）。
- **范围外改动**：scripts/verify_ui.py 的语言断言随四种语言模型改写（原断言「zh-HK 回退 zh-CN」「标签为中国香港」已失效）；scripts/ 原列入「明确不动」，属经确认后的执行期扩围，已在简报中披露。
- **数据事故与恢复**：批量补语言时脚本把 9 份 i18n.json 误写成空对象。obox/app/management/settings 从 git 恢复；rdp 从 tmp/rdp_repo、webapp 从 tmp/webapp_repo 恢复；demo/chartdemo/pickerdemo 无备份，按 views 与 extension.py 里的键位重建（demo 的 note.title 对齐 verify_ui 的「示范笔记」，其余键值按上下文补齐），与原值可能有措辞差异。
- **评审后新增遗留**：源码运行时自启动开关仍可点（设置视图没有通用禁用能力，点了会回滚并提示）；壳层 picker/title_bar/confirm_dialog 的用户可见中文未迁移（文件在白名单外）；chartdemo 图内文字需给扩展暴露语言；installer/obox.nsi 卸载不清理 HKCU Run 键；demo/rdp/webapp 的 extension.json 已改占位符但它们在 .gitignore 里，要各自仓发版才生效。
- **建议类**：obox/app.py 的 _locale_labels 已无引用、若干 i18n 死键（dialog.pick、settings.item.version.desc 等）、tray 与 close_dialog 的回退逻辑重复、translator 类型标注可收窄、test_autostart 有一条断言恒真，都留待清理。
- review.md 已生成，严重项 0。
- `.agents/skills/obox-test/scripts/check_all.py` 未跑（T12）。
- 收尾合并时按 delta-spec 改写 spec.md 的 6 条需求、按 delta-design 更新 design.md 的 D43/D15 并新增 D46/D47、按 delta-arch 更新 docs/arch.md 第 4、7 节。
