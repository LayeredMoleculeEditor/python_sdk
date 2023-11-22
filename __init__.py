from typing import TypedDict
import aiohttp

class Atom(TypedDict):
    element: int
    position: list[float, float, float]

type Atoms = dict[int, Atom | None]

class Bonds(TypedDict):
    indexes: list[tuple[int, int]]
    values: list[float | None]

class Molecule(TypedDict):
    atoms: Atoms
    bonds: Bonds

class Workspace:
    def __init__(self, server: str, name: str) -> None:
        self.__name__ = name
        self.__session__ = aiohttp.ClientSession(f"{server}")

    def __request__(self, method: str, path: str, **kargs):
        return self.__session__.request(method, f"/workspaces/{self.__name__}{path}", **kargs)

    async def create(self):
        resp = await self.__request__("post", "", data="null", headers = {"Content-Type": "application/json"})
        if resp.ok:
            return await resp.text()
        else:
            raise RuntimeError(await resp.text())

    async def remove(self):
        resp = await self.__request__("delete", "")
        if resp.ok:
            content = await resp.text()
            await self.__session__.close()
            return content
        else:
            raise RuntimeError(f"Failed to remove target workspace: {await resp.text()}")

    async def export(self):
        return await (await self.__request__("get", "/export")).json()

    async def get_stacks(self) -> list[int]:
        return await (await self.__request__("get", "/stacks")).json()
    
    async def get_stack(self, stack_id: int) -> Molecule:
        return await (await self.__request__("get", f"/stacks/{stack_id}")).json()
    
    async def clone_stack(self, stack_id: int) -> int:
        return await (await self.__request__("post", f"/stacks/{stack_id}/clone_stack")).json()
    
    async def is_stack_writable(self, stack_id: int) -> bool:
        return await (await self.__request__("get", f"/stacks/{stack_id}/writable")).json()
    
    async def overlay_fill_layer(self, stack_id: int):
        return await self.__request__("put", f"/stacks/{stack_id}", json={
            "Fill": {}
        })
        
    async def write_to_layer(self, stack_id: int, atoms: Atoms, bonds: Bonds):
        return await self.__request__("patch", f"/stacks/{stack_id}", json=(atoms, bonds))