from typing import Any, Dict, List, Optional

class KVStore(dict):
    def __init__(self) -> None:
        dict.__init__(self)
    
    def get(self, key: str) -> Optional[Any]:
        return dict.get(self, key)

    def set(self, key: str, value: Any) -> None:
        self[key] = value

    def delete(self, key: str) -> None:
        if key in self:
            del self[key]

    def exists(self, key: str) -> bool:
        return key in self

    def keys(self) -> List[str]:
        return list(dict.keys(self))

    def values(self) -> List[Any]:
        return list(dict.values(self))

    def items(self) -> List[tuple]:
        return list(dict.items(self))

    def clear(self) -> None:
        dict.clear(self)