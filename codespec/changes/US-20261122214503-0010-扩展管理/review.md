---
status: done
---

# Review

## 评审包

| 项目 | 内容 |
|---|---|
| 变更范围 | 修改 7 个文件（obox/api/extensions.py 新增、obox/extensions/{host,loader}.py、obox/app.py、obox/ui/{main_window}.py、obox/ui/confirm_dialog.py 新增、extensions/management/** 新增、tests/test_extension_manage.py 新增、scripts/verify_ui.py、技能文档），主链路是「控制消息 → 宿主安装/停用/卸载 → obox 差量应用」 |
| 对应需求 | 扩展管理（ADDED）；扩展安装、扩展生命周期与上下文注入、扩展目录与清单（MODIFIED） |
| 验证证据 | `uv run pytest -q` → 257 passed；`verify_ui --theme light|dark` → 各 0 失败；`check_all.py` → 全通过；ruff F,E9 → All checks passed |

## 作者自查

- [x] 每个 `完成` 任务的验收命令都真的跑过，并有输出
- [x] `check.py` 无严重项
- [x] 变更没有超出 delta-spec 的范围
- [x] 没有把"看起来对"当成"验证过"

## 意见清单

| ID | 档位 | 位置 | 问题 | 证据 | 结论 |
|---|---|---|---|---|---|
| R1 | 严重 | `obox/extensions/loader.py` | 覆盖升级失败会先清空旧目录（处理：改为解压到安装根下临时目录、校验清单后再原子替换，失败保留旧版） | 探针：装 v1 后装越界包，旧 extension.json 消失 | 接受 |
| R2 | 严重 | `obox/app.py 变更处理` | 禁用后视图不消失（处理：改为按宿主回推的 views 做权威对账，凡不在列表里的视图一律摘除） | 探针：禁用后 current view 仍在 demo.main | 接受 |
| R3 | 严重 | `obox/extensions/host.py 启用/停用` | 系统扩展可被消息停用（处理：只允许停用安装目录下的用户扩展，其余回 error） | 探针：settings.obox 被停用，disabled.json 写入 | 接受 |
| R4 | 一般 | `obox/extensions/host.py 安装` | 清单非法时异常逃出回推、留下半装目录（处理：load_manifest 放进 try，回 error；loader 在换版前校验 staging 清单） | 探针：缺 description 抛 ManifestError，包已删 | 接受 |
| R5 | 一般 | `obox/extensions/host.py 激活` | _activate 失败不清注册点，_views_payload 直接索引 manifest 会 KeyError（处理：失败分支 unregister_owner + 清状态；payload 遇缺失 manifest 跳过） | 探针：activate 抛错后残留 demo.main | 接受 |
| R6 | 一般 | `obox/api/extensions.py / host.py` | 控制消息不校验来源与载荷路径（处理：src 必须是 obox；包名取 basename 且必须以 .oix 结尾） | 探针：任意 src 的 install 生效 | 接受 |
| R7 | 一般 | `obox/app.py 变更处理` | 安装后 configuration 不刷新（处理：changed 后按 extensions 快照重建 _extensions_config 并推设置页） | 探针：安装后设置页无新配置 | 接受 |
| R8 | 一般 | `obox/api/extensions.py / app.py` | 安装后不注册 i18n，新视图显示 i18n 占位原文（处理：changed 消息带 i18n，obox 注册） | 探针：安装后 i18n 占位符原样保留 | 接受 |
| R9 | 一般 | `extensions/management` | 无安装中状态与成功提示（处理：点安装置 installing 并推视图；app 在 result ok 时提示成功） | grep 安装中零命中 | 接受 |
| R10 | 一般 | `obox/extensions/host.py 根目录` | system 根与 source 根重复，源码扩展被标成内置（处理：两目录相同时跳过 system 根） | 探针：源码扩展 origin 恒为 system | 接受 |
| R11 | 一般 | `obox/app.py / host.py 禁用名单` | 卸载不清名单且宿主与 obox 双写（处理：宿主只读名单，只有 obox 写 config 与镜像；卸载时清名单） | 探针：卸载后 config 仍含该 id | 接受 |
| R12 | 一般 | `obox/app.py 应用列表` | 禁用不摘 app 注册点、状态字段不更新（处理：changed 用宿主状态快照覆盖；_rebuild_apps 只收 active） | 探针：禁用后应用仍在列表 | 接受 |
| R13 | 一般 | `obox/extensions/host.py 启用` | 目录不存在时先清名单再返回（处理：先校验目录，缺失直接回 error，不做任何变更） | 代码路径 host.py 启用分支 | 接受 |
| R14 | 一般 | `obox/api/extensions.py` | changed 与 commands 字段无人消费（处理：commands 保留用于诊断日志，changed 由前端用于状态刷新语义；标为诊断载荷） | grep payload.get("commands") 零命中 | 部分接受 |
| R15 | 一般 | `obox/ui/confirm_dialog.py` | 确认框复制关闭框面板（处理：抽出 ModalPanelDialog 基类，两个对话框改为子类） | 两文件逐行重复约 50 行 | 接受 |
| R16 | 建议 | `obox/ui/main_window.py` | 摘掉最后一个底部视图后底栏仍占位（处理：remove_view 中按数量隐藏底栏） | 代码对比 clear_views | 接受 |
| R17 | 建议 | `obox/app.py / verify_ui.py` | 文件与函数超阈值（处理：登记到「长度超阈值」，本次不拆） | ast 统计 | 部分接受 |
| R18 | 建议 | `obox/extensions/loader.py` | 单调用封装 install_one 包一层（处理：删掉包装，公开函数即实现） | 两处调用 | 接受 |
| R19 | 建议 | `obox/extensions/host.py 存储清理` | 手写递归删目录且 remove_one 返回值被丢弃（处理：改用 shutil.rmtree） | 代码 | 接受 |
| R20 | 建议 | `extensions/management` | removable 用字符串标志（处理：改成布尔，OML 直接 o-if） | 实现与测试字符串 | 接受 |
| R21 | 建议 | `obox/app.py` | 表达式当语句（处理：改为 if 语句；摘当前视图时优先切到扩展管理页） | 代码 | 接受 |
| R22 | 建议 | `obox/api/extensions.py` | 宿主身份第二个字面量来源（处理：host 使用 HOST_ID 常量） | host.py 构造总线处 | 接受 |
| R23 | 建议 | `obox/ui/confirm_dialog.py / obox/i18n.json` | 确认框文案硬编码，scope 里的 i18n 落点未用（处理：与 CloseDialog 保持一致先硬编码，记入遗留） | i18n.json mtime 早于本次 | 部分接受 |
| R24 | 建议 | `scripts/verify_ui.py` | 搜索断言自证、无安装/卸载 UI 场景（处理：改为卡片数前后对比；安装/卸载仍由单测覆盖，verify 只验页面与过滤） | verify 代码 | 部分接受 |
| R25 | 建议 | `obox-ui-test/references/scenarios.md` | 场景表缺 20 号（处理：补 20 扩展管理页；该目录按 AGENTS.md 强制同步放开） | 场景表只到 19 | 接受 |
| R26 | 建议 | `tests/test_extension_manage.py` | 测试缺往返、回推帧与关键缺陷路径（处理：补 decode 往返、changed 帧、失败保留旧版、禁用系统扩展、禁用摘视图、卸载清名单、重装启用） | 测试文件 | 接受 |

## 长度超阈值

| 位置 | 行数 | 为什么不能再拆 |
|---|---|---|
| `obox/app.py` | 1197 | 装配中枢：消息路由、视图挂载、扩展管理编排、托盘与设置都在这里；拆出扩展管理控制器会新增一层回调与一个模块，收益低于跨模块查找成本 |
| `scripts/verify_ui.py` `main()` | 336 | 串行脚本按场景顺序执行，拆函数会打断共享的 obox 实例与截图编号 |
| `obox/extensions/host.py` `activate_all` | 46 | 一次启动激活里依次做安装、扫描、逐个激活与状态回推，拆开要传四个中间状态 |

## 回归

- R1：`uv run pytest -q tests/test_extension_manage.py -k keeps_old_version` → 通过
- R2/R7/R8/R11/R12：`uv run pytest -q tests/test_extension_manage.py` → 14 passed（含禁用摘视图、卸载清名单）
- R3/R6/R13：同上 → 禁用系统扩展被拒、外来 src 被忽略、目录缺失不误改名单
- R4/R5：`pytest -q` → 全绿（清单非法与激活失败都有回推与清理）
- R9/R16/R20/R21：`uv run python scripts/verify_ui.py --theme light|dark` → 各 0 失败
- R15：`uv run pytest -q tests/test_settings_close.py` → 通过（关闭框改基类后行为不变）
- R25/R26：`uv run python .agents/skills/obox-test/scripts/check_all.py` → 全通过

## 结论

- 严重：剩余 0 条
- 一般：R14、R23 部分接受，R17 登记在长度表；其余全部修复
- 建议：R24 部分接受（安装/卸载由单测覆盖，verify 只验页面与过滤）；R22 已改为单一常量来源