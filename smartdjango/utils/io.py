import json
import pickle

from typing import Protocol, cast


class SupportsWriteStr(Protocol):
    def write(self, __s: str) -> object:
        ...


class SupportsWriteBytes(Protocol):
    def write(self, __s: bytes) -> object:
        ...


def json_load(filepath: str):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def json_loads(s: str):
    return json.loads(s)


def json_dumps(obj, indent=2) -> str:
    return json.dumps(obj, indent=indent, ensure_ascii=False)


def json_save(obj, filepath: str):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(obj, cast(SupportsWriteStr, f), indent=2, ensure_ascii=False)


def jsonl_load(filepath: str):
    lines = file_load(filepath).split('\n')  # 读取整个文件并按行分割
    lines = list(filter(lambda line: line.strip(), lines))  # 去掉空行
    lines = list(map(lambda line: json_loads(line), lines))  # 每行解析成 JSON 对象
    return lines


def file_load(filepath: str) -> str:
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def file_save(filepath: str, content: str, append=False):
    with open(filepath, 'a+' if append else 'w', encoding='utf-8') as f:
        f.write(content)


def pkl_load(filepath: str):
    return pickle.load(open(filepath, "rb"))


def pkl_save(obj, filepath: str):
    pickle.dump(obj, cast(SupportsWriteBytes, open(filepath, "wb")))
