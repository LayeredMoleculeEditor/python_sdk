from typing import TypedDict
from requests import Session

session = Session()

class Config(TypedDict):
    prefix: str

config: Config = {
    "prefix": "http://localhost:10810"
}

class Workspace:
    def __init__(self, name: str) -> None:
        self.__name__ = name

    def __request__(self, method: str, path: str, *args, **kargs):
        return session.request(method, f"{config['prefix']}/workspaces/{self.__name__}{path}", *args, **kargs)

    @staticmethod
    def create(name: str):
        response = session.post(f"{config['prefix']}/workspaces/{name}", data="null", headers={
            "Content-Type": "application/json"
        })
        if response.ok:
            return Workspace(name)
        else:
            raise RuntimeError(response.text)

    def remove(self):
        return self.__request__("delete", "")

    def export(self):
        return self.__request__("get", "/export").json()

    def get_stacks(self):
        return self.__request__("get", "/stacks").json()
    
    def get_stack(self, stack_id: int):
        return self.__request__("get", f"/stacks/{stack_id}").json()
    
    def clone_stack(self, stack_id: int) -> int:
        return self.__request__("post", f"/stacks/{stack_id}/clone_stack").json()
    