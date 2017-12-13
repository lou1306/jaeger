from collections import OrderedDict
from typing import Optional, Dict

class Inventory(OrderedDict):
    _letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)        

    def add(self, item: 'Item') -> Optional[str]:
        s = self.next_empty()
        if s:
            self[s] = item
            return s
        else:
            return None
    
    def remove(self, item: 'Item') -> None:
        keys = [k for k in self.keys() if self[k] is item]
        for key in keys:
            del self[key]

    def next_empty(self):
        for slot in self._letters:
            if slot not in self:
                return slot
        return None
    
    def sorted(self) -> Dict[type, 'Inventory']:
        categories = set(item.category for item in self.values())
        out = {}
        for cat in categories:
            out[cat] = Inventory({key: value for key, value in self.items() if value.category == cat})
        return out

    def filter(self, category: 'Item') -> 'Inventory':
        if category:
            return Inventory({key: value for key, value in self.items() if value.category == category})
        else:
            return self.copy()

    def get_view(self, describer) -> Dict[str, 'Item']:
        return {self.pretty_print(key, describer): self[key] for key in self}

    def pretty_print(self, key, describer) -> str:
        return "{} - {}".format(key, describer(self[key]))