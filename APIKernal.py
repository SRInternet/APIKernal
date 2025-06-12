import aiohttp
import asyncio
from typing import Any, Dict, List, Optional, Union, Tuple
import json
import re

def parse_response(data: Any, paths: Union[str, List[str]]) -> Any:
    """
    解析响应数据
    
    :param data: 要解析的数据 (通常是dict或list)
    :param paths: 单个路径字符串或路径字符串列表
    :return: 解析结果，结果类型根据路径和数据类型决定
    """
    # 核心：通过正则表达式，识别索引和切片语法
    index_pattern = re.compile(r'\[(.*?)\]')

    def resolve_path(obj: Any, parts: List[str]) -> Union[Any, List[Any]]:
        """递归解析路径：返回最自然的类型"""
        if not parts or obj is None:
            return obj
            
        current = parts[0]
        remaining = parts[1:]
        
        # 检查当前部分是否包含索引/切片语法
        match = index_pattern.search(current)
        if match:
            # 提取索引/切片表达式
            index_expr = match.group(1)
            # 获取字段名（索引前的部分）
            field = current[:match.start()].strip()
            
            # 如果字段名不为空，先访问该字段
            if field:
                if isinstance(obj, dict) and field in obj:
                    obj = obj[field]
                elif isinstance(obj, (list, tuple)) and field.isdigit():
                    obj = obj[int(field)]
            
            # 处理通配符 (*) 或索引/切片
            if index_expr == '*':
                # 通配符处理，展开所有元素
                if not isinstance(obj, (list, tuple)):
                    return None
                
                results = []
                for item in obj:
                    result = resolve_path(item, remaining)
                    if isinstance(result, list):
                        results.extend(result)
                    else:
                        results.append(result)
                return results
            elif ':' in index_expr:
                # 切片处理
                indices = index_expr.split(':')
                try:
                    start = int(indices[0]) if indices[0] else 0
                    end = int(indices[1]) if len(indices) > 1 and indices[1] else len(obj)
                    step = int(indices[2]) if len(indices) > 2 and indices[2] else 1
                    
                    results = []
                    for item in obj[start:end:step]:
                        result = resolve_path(item, remaining)
                        if isinstance(result, list):
                            results.extend(result)
                        else:
                            results.append(result)
                    return results
                except (ValueError, TypeError):
                    return None
            else:
                # 单个索引处理
                try:
                    idx = int(index_expr)
                    return resolve_path(obj[idx], remaining)
                except (ValueError, TypeError, IndexError):
                    return None
                
        # 处理常规路径
        if isinstance(obj, dict) and current in obj:
            return resolve_path(obj[current], remaining)
            
        # 解析为数组索引
        if isinstance(obj, (list, tuple)) and current.isdigit():
            try:
                idx = int(current)
                return resolve_path(obj[idx], remaining)
            except (ValueError, IndexError):
                return None
            
        # 分割点路径
        if '.' in current:
            sub_paths = current.split('.')
            return resolve_path(obj, sub_paths + remaining)
            
        return None
    
    # 处理单个路径或路径列表
    if isinstance(paths, str):
        # 对于单个路径，返回最自然的类型
        path_parts = [part.strip() for part in paths.split('.') if part.strip()]
        return resolve_path(data, path_parts)
    else:
        # 对于多个路径，返回结果列表
        return [resolve_path(data, [part.strip() for part in p.split('.') if part.strip()]) 
                for p in paths]

# 请求函数
async def request_api(
    api: str,
    paths: Optional[Union[str, List[str]]] = None,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    payload: Optional[Dict[str, Any]] = None,
    timeout: int = 15
) -> Any:
    """
    异步执行API请求并解析响应数据
    
    :param api: API端点URL
    :param paths: 要解析的一个或多个路径
    :param method: HTTP方法 (GET, POST, etc.)
    :param headers: 请求头
    :param payload: 请求负载(对于POST/PUT等)
    :param timeout: 超时时间(秒)
    :return: 解析后的数据
    """
    headers = headers or {}
    payload = payload or {}
    
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            # 根据方法选择合适的请求方式
            if method.upper() in ["GET", "HEAD"]:
                async with session.request(method, api, headers=headers, params=payload) as response:
                    return await handle_response(response, paths)
            else:
                async with session.request(method, api, headers=headers, json=payload) as response:
                    return await handle_response(response, paths)
    except asyncio.TimeoutError:
        raise RuntimeError(f"API请求超时: 超过 {timeout} 秒")
    except aiohttp.ClientError as e:
        error_msg = f"API请求失败: {str(e)}"
        if hasattr(e, 'status') and e.status:
            error_msg += f" (状态码: {e.status})"
        raise RuntimeError(error_msg)

# 响应处理函数
async def handle_response(response: aiohttp.ClientResponse, paths: Optional[Union[str, List[str]]] = None) -> Any:
    """处理响应并返回解析后的数据（由 request_api 调用）"""
    content = await response.text()
    
    if not response.ok:
        error_msg = f"API返回错误: {response.status} {response.reason}"
        if content:
            error_msg += f"\n错误详情: {content[:200]}..."
        raise RuntimeError(error_msg)
    
    # 解析JSON
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        data = content
    
    # 没有指定路径，返回原始数据
    if not paths:
        return data
    
    # 解析指定的路径
    return parse_response(data, paths)