# TypeScript 代码规范与坏味道

## 规范

- 类型优先于断言：能从运行时数据推出来的，用类型守卫/校验库，而不是 `as`
- 禁用 `any`：确实未知时用 `unknown` 再收窄
- 严格模式：`strict`、`noUncheckedIndexedAccess`、`exactOptionalPropertyTypes` 能开就开
- 联合类型：用可辨识联合（判别字段）表达状态，代替布尔开关组合
- 导出：只导出公共 API；内部类型不进 barrel 文件
- 泛型：约束为具体能力（`extends`），不要为了"通用"留下无约束泛型
- 命名：类型与接口 `PascalCase`，不加 `I` 前缀；布尔用 `is/has/can` 开头

## 坏味道

| 坏味道 | 识别信号 | 改法 |
|---|---|---|
| `any` 泄漏 | 函数签名或返回值出现 `any` | 换具体类型或 `unknown` + 守卫 |
| `as` 代替校验 | `JSON.parse(x) as T` | 运行时校验（zod 等）后再赋值 |
| 非空断言滥用 | `foo!.bar` | 显式判空或收窄 |
| `@ts-ignore` | 直接压错误 | 修类型，必要时 `@ts-expect-error` 并写原因 |
| 布尔开关组合 | `{loading, error, data}` 各自真假 | 可辨识联合 `{status:'loading'|'ok'|'error'}` |
| 可选属性堆叠 | 一堆 `?:` 却总有隐含约束 | 拆成联合类型 |
| `Record<string, any>` 万能表 | 到处传 map | 定义具体键或索引签名约束 |
| 类型与运行时脱节 | 接口改了但校验没改 | 校验与类型同源（schema 推导类型） |
| 循环依赖 | 模块互引 | 抽公共类型模块 |
| 过度泛型 | `<T extends unknown>` | 具体类型或去掉泛型 |

## 特别注意

- `enum` 与 `const enum` 在打包与 `isolatedModules` 下行为不同，跨包导出时优先字面量联合。
- 改类型时先看是否有 `.d.ts` 对外发布：类型是公共契约，破坏性变更要标注。
