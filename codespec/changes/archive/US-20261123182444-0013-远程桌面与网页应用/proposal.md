---
status: done
---

# 远程桌面与网页应用 · rdp 与 webapp 两个用户扩展

## 背景

仿照 web 版 obox 的 rdp 与 webapp 扩展，在 Python obox 里重做两个用户扩展：一个管理 RDP 连接并在 Windows 上拉起 mstsc，一个把内部站点用 Chrome 的应用模式打开、每条目独立 profile。现有扩展 API 缺少「扩展读取自己配置」的能力，webapp 的选项需要它，因此一并补上。

## 目标

- 远程桌面扩展：App 卡片 + 连接列表 + 搜索 + 新建/编辑/删除确认/打开
- 网页应用扩展：App 卡片 + 站点列表 + 搜索 + 新建/编辑/删除确认/打开
- 密码用 Windows DPAPI 加密保存，可勾选是否记住
- RDP 打开走 .rdp（记住密码时写入 DPAPI 密文）+ 脱离 obox 进程树的 mstsc；webapp 打开走 Chrome `--app` + 独立 `--user-data-dir`
- 宿主把扩展自己的配置值下发给扩展，设置页沿用现有扩展配置
- 两个扩展都带中文（zh-CN）与英文（en-US）文案

## 范围

**做：**

- 新增 `extensions/rdp`：extension.json、extension.py、views/main.oml、i18n.json、assets 图标
- 新增 `extensions/webapp`：同上，附带 contributes.configuration（profile 根目录、单站点数据上限）
- 宿主新增配置下发：扩展激活后与配置变更时，把该扩展的 configuration 当前值发给它
- Windows 能力封装：DPAPI 加解密、cmdkey 预置凭据、mstsc 与 Chrome 的脱离式启动、Chrome 路径探测
- 连接/站点数据存扩展 storage 的 JSON；密码单独加密文件
- 测试：字段校验、.rdp 文本、命令拼装、Chrome 探测、配置下发

**不做：**

- 不内置浏览器，不自动安装 Chrome，不回退 Edge
- 不做批量导入导出、分组、多语言界面（只 zh-CN / en-US 文案）
- 不做 RDP 窗口内嵌（用系统 mstsc）
- 不改扩展清单格式（app 与 configuration 都复用现有字段）

## 需求草案

1. 远程桌面扩展以 App 卡片「远程桌面」出现，打开后是连接列表，顶部搜索，右上「新建连接」
2. 连接字段：名称（必填且唯一）、主机（必填）、端口（默认 3389，1–65535）、用户名、域、记住密码
3. 点「打开」生成 .rdp、用 cmdkey 预置凭据、以脱离进程的方式拉起 mstsc；obox 退出不影响已打开的会话
4. 勾选记住密码时用 DPAPI 加密保存；不勾选则不落盘；解密失败提示重新输入
5. 网页应用扩展以 App 卡片「网页应用」出现，打开后是站点列表、搜索、新建
6. 站点字段：名称（必填唯一）、URL（必填，http/https）、忽略证书错误（可选）
7. 点「打开」用 Chrome 的 app 模式与独立 profile 目录启动，脱离 obox 进程树；找不到 Chrome 时明确提示
8. 设置页可配：profile 根目录（默认扩展 storage 下）、单站点数据上限（0/512/1024/2048 MB）
9. 宿主在扩展激活后与配置变更时下发该扩展的配置值；扩展据此决定 profile 根目录与上限
10. 两个扩展在非 Windows 平台打开时提示「仅支持 Windows」

## 关键取舍

- 用 App 卡片承载界面：与参考实现一致，AppWindow 里渲染扩展的 OML，不需要新的容器
- 数据存扩展 storage 的 JSON：条目量小，不引入 sqlite；密码只存 DPAPI 密文
- 脱离式启动：Windows 上用 DETACHED_PROCESS + CREATE_NEW_PROCESS_GROUP，配合 `cmd /c start`，保证 obox 退出不带走会话
- 配置下发用一条新消息（obox → 扩展）：设置页不变，扩展在激活后立刻拿到值，变更时再推
- .rdp 只写常用字段：full address、username、domain、authentication level、prompt for credentials；其余用 mstsc 默认
- Chrome 探测顺序：注册表 App Paths → Program Files 常见路径 → PATH；找不到时报错而不是静默

## 与基线的冲突

- 基线「扩展配置贡献」只描述设置页渲染与写入，没有扩展读取自己配置的通道，需 ADDED 一条配置下发
- 基线「扩展目录与清单」新增两个源码扩展，属正常使用，无需改
- 基线「扩展开发技能」需补 App 卡片 + 配置读取示例
- 基线「i18n 注册与占位替换」要求 zh-CN 必填，本次两个扩展都满足

## 假设

- 扩展作者用 chenzhi（与参考实现一致），id 为 rdp.chenzhi 与 webapp.chenzhi
- .rdp 字段取常用子集，其余交给 mstsc 默认
- 密码加密失败时按「不记住」处理并提示
- 配置下发消息在实现时定名，方向是 obox → 扩展
