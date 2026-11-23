---
status: done
---

# Validation

## 检查范围

| 文件 | 存在 | 结论 |
|---|---|---|
| delta-spec.md | 是 | 4 条 ADDED + 1 条 MODIFIED |
| delta-design.md | 是 | 7 行改动、4 条风险 |
| delta-arch.md | 是 | 时序图与类图齐备 |
| task.md | 是 | 6 个任务覆盖全部需求 |
| scope.md | 是 | 白名单 9 条 |

## 问题清单

| ID | 档位 | 位置 | 问题 | 处理 |
|---|---|---|---|---|
| V1 | 严重 | scripts/build_exe.py | Nuitka 的 --output-dir 必须用等号形式，首版构建直接报错 | 已修复 |
| V2 | 严重 | build/obox.nsi | NSIS 脚本无 BOM 报 Bad text encoding | 已修复：utf-8-sig 写出 |
| V3 | 严重 | obox/extensions/supervisor.py | 安装版用 sys.executable 以 -m 启动宿主，exe 不认 -m，扩展不激活 | 已修复：frozen 时走 --extension-host 入口 |
| V4 | 一般 | obox/extensions/supervisor.py | frozen 检测只靠 __compiled__ 不可靠 | 已改为三重判断（frozen/__compiled__/exe 名） |
| V5 | 严重 | installer/obox.nsi | NSIS 缺 UserInfo.nsh，管理员探测编不过 | 已改为 HKLM 写入探测 |
| V6 | 严重 | installer/obox.nsi | 显式 /ALLUSERS 被已有 HKCU 安装覆盖，范围选择失效 | 增加 ScopeExplicit，显式参数优先 |
| V7 | 严重 | installer/obox.nsi | 卸载器 $INSTDIR 取默认值，删不掉安装目录 | 改用 $EXEDIR |
| V8 | 严重 | installer/obox.nsi | 卸载器在安装目录内运行，自删除失败 | 复制到 TEMP 带 /FROMTEMP 再执行，延时清理 |
| V9 | 一般 | installer/obox.nsi | 32 位注册表视图写进 WOW6432Node | 增加 SetRegView 64 |
| V10 | 严重 | installer/obox.nsi | 目录页默认路径不跟随范围选择，选所有用户仍显示用户目录 | 增加 DirectoryPre，在目录页显示前按范围重设默认值 |
| V11 | 严重 | installer/obox.nsi | 自定义卸载流程自复制路径为空，卸载无效果 | 删除自复制逻辑，依赖 NSIS 自动复制卸载器，RMDir /r 清目录 |

## 遗留

- 本机账号可静默提权，管理员校验分支未在标准用户上实测；标准用户下选择所有用户会提示并中止。