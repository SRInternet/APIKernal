# APIKernal 模块

API的请求、高级响应解析和批处理一步到位。
> [!Important]
> APIKernal 模块目前处于开发阶段，[路径解析语法](#路径解析语法)中的部分功能可能尚未完全实现或不稳定。若您遇到问题，请及时发布 [New Issue](https://github.com/SRInternet/APIKernal/issues/new) ，感谢理解。

## 功能特性

- 使用aiohttp进行异步API请求
- 支持JSON响应的**高级路径**解析语法
- 支持GET/POST/PUT/DELETE等多个请求方法方法
- 超时处理和错误管理
- 支持批量处理多个路径

## 安装要求

```bash
pip install aiohttp
```

## 基本用法

```python
from APIKernal import request_api

# 简单API请求
result = await request_api("https://api.example.com/data", paths="items[0].name")

# 批量处理
results = await request_api("https://api.example.com/data", paths=["items[*].id", "metadata.version"])

```

## 路径解析语法

参见 [Wiki：复杂路径规范](https://github.com/SRON-org/APICORE/wiki/Complex-Configuration)

## API 文档

### `request_api(api, paths=None, method="GET", headers=None, payload=None, timeout=15)`

发起异步API请求并解析响应。

**参数:**
- `api`: API端点URL
- `paths`: 要从响应中提取的单个路径字符串或路径列表
- `method`: HTTP方法 (GET, POST等)
- `headers`: 请求头
- `payload`: 请求负载 (用于POST/PUT)
- `timeout`: 请求超时时间(秒)

**返回:**
解析后的响应数据，如果提供多个路径则返回数据列表

### `parse_response(data, paths)`

使用路径表达式解析数据(通常是字典/列表)。

**参数:**
- `data`: 要解析的数据 (字典或列表)
- `paths`: 单个路径字符串或路径列表

**返回:**
与路径匹配的解析结果

## 错误处理

模块会抛出 `RuntimeError` 异常，当遇到:
- 请求超时
- HTTP错误

模块会返回 `NoneType` 值，当遇到:
- 无效的JSON响应
- 路径解析失败

## 系统要求

- Python 3.8+
- aiohttp

## 许可证

MIT
