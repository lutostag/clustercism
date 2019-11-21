import io
import os
import re
import requests
import tarfile
from tenacity import retry, stop_after_attempt

EXERCISE_URL = "https://exercism.io/tracks/{}/exercises/{}/solutions"
SOLUTION_REGEX = re.compile("/solutions/([a-z0-9]+)")
PAGE_REGEX = re.compile("/tracks/[a-z-]*/exercises/[a-z-]*/solutions\?page=([0-9]+)")
SOLUTION_URL = "https://api.exercism.io/v1/solutions/{}"
TOKEN = os.environ["EXERCISM_APITOKEN"]
IGNORES = [".gitignore", "Cargo.toml", "README.md", "tests/anagram.rs"]


@retry(stop=stop_after_attempt(7))
def http_get(*args, **kwargs):
    return requests.get(*args, **kwargs)


class Solutions:
    def __init__(self, lang, exercise):
        self.base_url = EXERCISE_URL.format(lang, exercise)

    def download_all(self):
        for uuid in self.uuids():
            Solution(uuid).create_tar()

    def uuids(self):
        for page in self.pages():
            page.raise_for_status()
            for uuid in SOLUTION_REGEX.findall(page.text):
                yield uuid

    def pages(self):
        r = http_get(self.base_url)
        r.raise_for_status()
        yield r

        pages = (int(p) for p in PAGE_REGEX.findall(r.text))
        for p in range(2, max(pages)):
            yield http_get(self.base_url + "?page=" + str(p))


class Solution:
    def __init__(self, uuid):
        print(uuid)
        self.uuid = uuid

    def files(self):
        headers = {
            "user-agent": "clustercism/0.0.1",
            "content-type": "application/json",
            "authorization": f"Bearer {TOKEN}",
        }
        r = http_get(SOLUTION_URL.format(self.uuid), headers=headers)
        json = r.json()
        base_url = json["solution"]["file_download_base_url"]
        for filename in json["solution"]["files"]:
            if filename in IGNORES:
                continue
            r = http_get(base_url + filename, headers=headers)
            if r.status_code == 404:
                continue
            yield (filename, r.content)

    def create_tar(self):
        with tarfile.open(f"{self.uuid}.tar", "w") as tar:
            for (filename, content) in self.files():
                info = tarfile.TarInfo(name=filename)
                info.size = len(content)
                tar.addfile(info, io.BytesIO(content))


# Solutions("rust", "anagram").download_all()
# SOLUTION = "1191813d448a4d31ba68aed31b34f29a"
# Solution(SOLUTION).create_tar()
# for file_ in Solution(SOLUTION).files():
#    print(file_)

# for solution in Solutions('rust', 'anagram').uuids():
#    print(solution)
