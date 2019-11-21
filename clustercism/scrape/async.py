import aiohttp
import asyncio
import io
import os
import re
import requests
import tarfile
import itertools
from tenacity import retry, stop_after_attempt

EXERCISE_URL = "https://exercism.io/tracks/{}/exercises/{}/solutions"
SOLUTION_REGEX = re.compile("/solutions/([a-z0-9]+)")
PAGE_REGEX = re.compile("/tracks/[a-z-]*/exercises/[a-z-]*/solutions\?page=([0-9]+)")
SOLUTION_URL = "https://api.exercism.io/v1/solutions/{}"
TOKEN = os.environ["EXERCISM_APITOKEN"]
IGNORES = [".gitignore", "Cargo.toml", "README.md", "tests/anagram.rs"]

SESSION = aiohttp.ClientSession()


@retry(stop=stop_after_attempt(7))
async def http_get(reader, *args, **kwargs):
    async with SESSION.get(*args, **kwargs) as resp:
        resp.raise_for_status()
        return await getattr(resp, reader)()


class Solution:
    def __init__(self, uuid):
        self.uuid = uuid

    async def files(self):
        headers = {
            "user-agent": "clustercism/0.0.1",
            "content-type": "application/json",
            "authorization": f"Bearer {TOKEN}",
        }
        json = await http_get("json", SOLUTION_URL.format(self.uuid), headers=headers)
        base_url = json["solution"]["file_download_base_url"]
        for filename in json["solution"]["files"]:
            if filename in IGNORES:
                continue
            content = await http_get("read", base_url + filename, headers=headers)
            yield (filename, content)

    async def create_tar(self):
        with tarfile.open(f"{self.uuid}.tar", "w") as tar:
            async for (filename, content) in self.files():
                info = tarfile.TarInfo(name=filename)
                info.size = len(content)
                tar.addfile(info, io.BytesIO(content))


class Solutions:
    def __init__(self, lang, exercise):
        self.base_url = EXERCISE_URL.format(lang, exercise)

    async def download_all(self):
        uuids = await self.uuids()
        print(f"should have {len(uuids)}")
        tasks = await asyncio.gather(
            *[Solution(uuid).create_tar() for uuid in uuids], return_exceptions=True
        )
        print([task for task in tasks if task is not None])
        return tasks

    async def uuids(self):
        pages = await self.pages()
        return set(
            itertools.chain.from_iterable(
                (SOLUTION_REGEX.findall(page) for page in pages)
            )
        )

    async def pages(self):
        text = http_get("text", self.base_url)
        pages = (int(p) for p in PAGE_REGEX.findall(await text))

        return await asyncio.gather(
            *[
                http_get("text", self.base_url + "?page=" + str(p))
                for p in range(1, max(pages))
            ]
        )


async def async_main():
    try:
        await Solutions("rust", "anagram").download_all()
    finally:
        await asyncio.sleep(1)
        global SESSION
        await SESSION.close()


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_main())


main()
