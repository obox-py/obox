---
status: done
---

# Review

## 评审包

| 项目 | 内容 |
|---|---|
| 变更范围 | 新增 extensions/rdp 与 extensions/webapp（清单、extension.py、views/main.oml、i18n.json、图标）；obox/api/settings.py 增 EXTENSION_CONFIG_MSG；obox/app.py 下发配置、保留 App 窗口 ViewHandle、登记扩展目录；tests/test_extensions_process.py、tests/test_extension_config.py；verify 增两个 App 截图；obox-ext-dev 文档；obox/ui/components/input.py 加 password 属性 |
| 对应需求 | 远程桌面扩展、网页应用扩展（ADDED）；扩展配置贡献、扩展开发技能（MODIFIED） |
| 验证证据 | `pytest -q` → 290 passed；`verify_ui --theme light/dark` → 各 0 失败（新增 22_rdp、23_webapp）；`check_all.py` → 全通过 |

## 作者自查

- [x] 每个 `完成` 任务的验收命令都真的跑过，并有输出
- [x] `check.py` 无严重项
- [x] 变更没有超出 delta-spec 的范围（例外见 R1）
- [x] 没有把"看起来对"当成"验证过"

## 意见清单

| ID | 档位 | 位置 | 问题 | 证据 | 结论 |
|---|---|---|---|---|---|
| R1 | 一般 | `obox/ui/components/input.py` | 越界：给 Input 加 password 属性（3 行），scope 里原本不动；已向你申请扩范围但超时未答（待用户决策） | 代码 diff | 接受 |
| R2 | 一般 | `obox/app.py` | App 窗口原来没有 ViewHandle，扩展无法更新页面数据；已补装配时保留与 app. 加窗口 id 路由 | 探针：rdp-root 不存在 | 接受 |
| R3 | 一般 | `obox/app.py` | 扩展目录原先只在声明 views 时登记，只有 App 卡片的扩展加载不到 views/main.oml；已改为按 extensions 清单登记 | 探针：加载 OML 失败 | 接受 |
| R4 | 一般 | 清单配置 | 配置属性名不能驼峰（清单校验只允许小写），已把 profileRoot/limitMb 改成 profileroot/limitmb 并同步文档 | 清单校验报错 | 接受 |
| R5 | 建议 | i18n | 扩展 i18n 的 id 必须带扩展名前缀（与 settings 一致），已把 key 改成 rdp.* 与 webapp.* | 页面残留 i18n 占位符 | 接受 |
| R6 | 建议 | rdp | .rdp 与密码密文留在 storage/tmp，未做清理（mstsc 会话期间可能需要该文件；注释说明） | 设计取舍 | 接受 |
| R14 | 建议 | 两个扩展图标 | 原来是单色描边 SVG，用户要求多彩（处理：RDP 换深色边框 + 蓝紫渐变屏幕，webapp 换蓝色地球 + 绿色/黄色大陆与经纬线） | 用户反馈 | 接受 |
| R13 | 一般 | 两个扩展 | 删除改成确认框；RDP 表单改折叠分组（账号含用户名/密码/域）、子标题 16/600；托盘图标传错参数（TrayIcon 收到 QWidget）已修为 QIcon | 用户反馈 | 接受 |
| R11 | 一般 | 两个扩展表单 | 参数比 web 版少很多（处理：RDP 扩到 46 个字段并按组呈现、webapp 补 8 项；编辑按数据绑定回填） | 用户反馈 | 接受 |
| R10 | 一般 | `obox/ui/builder.py` | value/checked 属性原来不参与绑定，编辑无法回填（处理：按 state_accessors 的 setter 绑定；越界项） | 探针：字段为空 | 接受 |
| R9 | 一般 | `obox/ui/components/switch.py` | 滑块是 3px 圆角方块、尺寸 40×22，与容器不匹配（处理：改圆形滑块，尺寸对齐 36×20，越界项） | 用户截图反馈 | 接受 |
| R8 | 一般 | 两个扩展界面 | 新建/编辑原是页面内联表单，用户要求改模态框（处理：常驻 Modal + COMPONENT_MODIFY_MSG 控制可见，验证新增 24/25 截图） | 用户复核 | 接受 |
| R7 | 建议 | 两个扩展 | 打开路径未做端到端测试（会真的拉起 mstsc/Chrome）（只测参数与校验，真实连接靠人工验收） | 测试范围 | 接受 |

## 长度超阈值

| 位置 | 行数 | 为什么不能再拆 |
|---|---|---|
| `extensions/rdp/extension.py` | 330 | 状态机、存储、DPAPI、启动都在一处；拆开会让事件处理跨文件跳转 |

## 回归

- 单测：`uv run pytest -q` → 290 passed（含 DPAPI roundtrip、.rdp 文本、Chrome 参数、配置下发）
- 界面：verify 两套主题各 0 失败，App 页面截图见 tmp/pics/light_22_rdp.png 与 light_23_webapp.png
- 门禁：`check_all.py` → 全通过

## 结论

- 严重：剩余 0 条
- 一般：R1 待用户决策（越界）；R2、R3、R4 接受并已修
- 建议：R5 接受；R6、R7 接受并记录取舍