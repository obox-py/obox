# 语言规范索引

按任务涉及的文件扩展名取对应文档；跨语言项目读多份。这些文档约束**写法**，不覆盖项目的既有风格配置——项目有自己的 lint/format 配置时，以项目为准。

| 扩展名 | 语言 | 文档 |
|---|---|---|
| `.c` `.h` | C | [c.md](c.md) |
| `.cc` `.cpp` `.cxx` `.hpp` | C++ | [cpp.md](cpp.md) |
| `.java` | Java | [java.md](java.md) |
| `.py` `.pyi` | Python | [python.md](python.md) |
| `.go` | Go | [go.md](go.md) |
| `.rs` | Rust | [rust.md](rust.md) |
| `.js` `.jsx` `.mjs` `.cjs` | JavaScript | [js.md](js.md) |
| `.ts` `.tsx` | TypeScript | [ts.md](ts.md) |

用法：`df-solver` 在分派任务前先看该任务的`涉及文件`，读对应文档；派 subagent 时把要遵守的文档路径写进它的简报。
