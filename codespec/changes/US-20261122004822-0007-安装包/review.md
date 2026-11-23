---
status: done
---

# Review

## 评审包

| 项目 | 内容 |
|---|---|
| 变更范围 | Nuitka standalone 构建、NSIS 安装包、运行期路径解析、三根扩展扫描 |
| 对应需求 | 安装包构建、安装目录布局、运行期路径解析、系统扩展扫描、扩展目录与清单 |
| 验证证据 | 单个 dist/obox-1.0.0-setup.exe（34MB）；/CURRENTUSER 与 /ALLUSERS 静默安装各一次、均可卸载；安装树含 exe、.theme、extensions/{app,settings}；安装版启动后两个扩展激活 |
| 边界比对 | 改动落在 obox、scripts、installer、tests、docs、README、AGENTS、技能 |

## 意见清单

| ID | 档位 | 位置 | 问题 | 证据 | 结论 |
|---|---|---|---|---|---|
| R1 | 严重 | obox/extensions/supervisor.py | 安装版以 sys.executable -m 启动宿主，exe 不支持 -m | 安装后运行无 storage 目录，扩展未激活 | 接受 |
| R2 | 严重 | build/obox.nsi | 无 BOM 的 UTF-8 被 makensis 拒绝 | Bad text encoding 第 1 行 | 接受 |
| R3 | 一般 | scripts/build_exe.py | --output-dir 必须等号形式 | Nuitka 首轮失败 | 接受 |
| R5 | 严重 | installer/obox.nsi | 缺 UserInfo.nsh，管理员探测编不过 | makensis 报 could not find UserInfo.nsh | 接受 |
| R6 | 严重 | installer/obox.nsi | 显式 /ALLUSERS 被 HKCU 旧安装覆盖 | 装到 all 目录却写 HKCU | 接受 |
| R7 | 严重 | installer/obox.nsi | 卸载删不掉安装目录 | 卸载后目录仍在 | 接受 |
| R8 | 严重 | installer/obox.nsi | 卸载器无法自删除 | 安装目录残留 uninstall.exe | 接受 |
| R9 | 一般 | installer/obox.nsi | 注册表写进 WOW6432Node | reg query 64 位视图查不到 | 接受 |
| R10 | 严重 | installer/obox.nsi | 目录页默认值不随范围选择变化 | 用户反馈选所有用户仍装到用户目录 | 接受 |
| R11 | 严重 | installer/obox.nsi | 卸载器自复制路径为空导致卸载无效 | 卸载后目录与注册表仍在 | 接受 |

## 回归

- `uv run pytest -q` → 208 passed
- 单个 `dist/obox-1.0.0-setup.exe`：/CURRENTUSER 与 /ALLUSERS 各装一次、各卸一次 → 全部退出 0；目录含 exe/.theme/extensions；注册表分别写 HKCU 与 HKLM；卸载后目录与键均清除
- 两种范围的卸载 → 退出 0，安装目录与注册表键均清除
- 安装版运行 --exit-after → 退出 0；storage 下 app.obox 与 settings.obox 生成
- `check.py` 变更与基线 → 0

## 结论

- 严重：剩余 0
- 一般：0