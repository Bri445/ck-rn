import click
import requests
import config
import json
from loguru import logger
from assessment.solver import GradedSolver


class Skipera(object):
    def __init__(self, course: str, llm: bool):
        self.user_id = None
        self.course_id = None
        self.base_url = config.BASE_URL
        self.session = requests.Session()
        self.session.headers.update(config.HEADERS)

        # ✅ Parse cookies from env (string → dict)
        try:
            cookies = json.loads(config.COOKIES) if isinstance(config.COOKIES, str) else config.COOKIES
        except Exception:
            logger.error("Invalid cookies format. Please provide valid JSON.")
            cookies = {}
        self.session.cookies.update(cookies)

        self.course = course
        self.llm = llm
        if not self.get_userid():
            self.login()  # implementation pending

    def login(self):
        logger.debug("Trying to log in using credentials")
        # NOTE: config.EMAIL/config.PASSWORD are not used in Streamlit flow.
        # We rely on cookies provided by user.
        r = self.session.post(self.base_url + "login/v3", json={
            "code": "",
            "email": getattr(config, "EMAIL", ""),
            "password": getattr(config, "PASSWORD", ""),
            "webrequest": True,
        })
        logger.info(f"Login response status: {r.status_code}")
        try:
            logger.debug(f"Login response JSON: {r.json()}")
        except ValueError:
            logger.debug(f"Login response text: {r.text}")

    def get_userid(self):
        r = self.session.get(self.base_url + "adminUserPermissions.v1?q=my")
        logger.debug(f"get_userid status: {r.status_code}")
        try:
            j = r.json()
        except ValueError:
            logger.error(f"Failed to parse JSON from get_userid: status={r.status_code} body={r.text}")
            return False

        elements = j.get("elements")
        if not elements or not isinstance(elements, list):
            logger.error(f"No 'elements' list in response: {j}")
            if j.get("errorCode"):
                logger.error(f"Error Encountered: {j.get('errorCode')}")
            return False

        try:
            self.user_id = elements[0].get("id")
            logger.info(f"User ID: {self.user_id}")
        except Exception:
            logger.exception("Failed to extract user id")
            return False

        return True

    def get_modules(self):
        r = self.session.get(
            self.base_url + f"onDemandCourseMaterials.v2/?q=slug&slug={self.course}&includes=modules"
        )
        logger.debug(f"get_modules status: {r.status_code}")
        try:
            j = r.json()
        except ValueError:
            logger.error(f"Failed to parse JSON in get_modules: {r.status_code} {r.text}")
            return
        try:
            self.course_id = j["elements"][0]["id"]
            logger.debug(f"Course ID: {self.course_id}")
            modules = j.get("linked", {}).get("onDemandCourseMaterialModules.v1", [])
            logger.debug(f"Number of Modules: {len(modules)}")
            for x in modules:
                logger.info(f"{x.get('name')} -- {x.get('id')}")
        except Exception:
            logger.exception("Unexpected structure in get_modules response")

    def get_items(self):
        r = self.session.get(self.base_url + "onDemandCourseMaterials.v2/", params={
            "q": "slug",
            "slug": self.course,
            "includes": "passableItemGroups,passableItemGroupChoices,items,tracks,gradePolicy,gradingParameters",
            "fields": "onDemandCourseMaterialItems.v2(name,slug,timeCommitment,trackId)",
            "showLockedItems": "true"
        })
        logger.debug(f"get_items status: {r.status_code}")
        try:
            j = r.json()
        except ValueError:
            logger.error(f"Failed to parse JSON in get_items: {r.status_code} {r.text}")
            return

        items = j.get("linked", {}).get("onDemandCourseMaterialItems.v2", [])
        for video in items:
            logger.info(f"Watching {video.get('name')}")
            self.watch_item(video.get("id"))

    def watch_item(self, item_id):
        if not self.user_id:
            logger.error("No user_id available, cannot watch item")
            return
        r = self.session.post(
            self.base_url + f"opencourse.v1/user/{self.user_id}/course/{self.course}/item/{item_id}/lecture"
                            f"/videoEvents/ended?autoEnroll=false",
            json={"contentRequestBody": {}}
        )
        logger.debug(f"watch_item status: {r.status_code}")
        try:
            j = r.json()
        except ValueError:
            logger.debug(f"watch_item response not JSON: {r.text}")
            self.read_item(item_id)
            return

        if j.get("contentResponseBody") is None:
            logger.info("Not a watch item! Reading..")
            self.read_item(item_id)

    def read_item(self, item_id):
        if not self.course_id or not self.user_id:
            logger.error("Missing course_id or user_id; cannot mark read")
            return
        r = self.session.post(self.base_url + "onDemandSupplementCompletions.v1", json={
            "courseId": self.course_id,
            "itemId": item_id,
            "userId": int(self.user_id)
        })
        logger.debug(f"read_item status: {r.status_code}")
        if "Completed" not in r.text:
            logger.debug("Item may be a quiz/assignment or not marked completed")
            if "StaffGradedContent" in r.text and self.llm:
                logger.debug("Attempting to solve graded assessment..")
                solver = GradedSolver(self.session, self.course_id, item_id)
                solver.solve()


@logger.catch
@click.command()
@click.argument('slug')
@click.option('--llm', is_flag=True, help="Whether to use an LLM to solve graded assignments.")
def main(slug: str, llm: bool) -> None:
    skipera = Skipera(slug, llm)
    skipera.get_modules()
    skipera.get_items()


if __name__ == '__main__':
    main()
