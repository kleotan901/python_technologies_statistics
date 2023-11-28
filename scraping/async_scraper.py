import asyncio
import csv
import re
import time
from dataclasses import dataclass, fields, astuple
from typing import List

import aiohttp
from bs4 import BeautifulSoup
from tqdm.asyncio import tqdm

BASE_URL = "https://djinni.co"
URL = "https://djinni.co/jobs/?primary_keyword=Python"
JOBS_OUTPUT_CSV = "jobs.csv"


@dataclass
class Job:
    name: str
    salary: str
    experience: int
    views: int
    applications: int
    description: str


JOBS_FIELDS = [field.name for field in fields(Job)]


def get_num_pages(soup: BeautifulSoup) -> int:
    page_numbers = soup.select_one(".pagination.pagination_with_numbers")
    if page_numbers is None:
        return 1

    return int(page_numbers.select("li.page-item")[-2].text)


def parse_job_description(detail_page_soup: BeautifulSoup) -> str:
    description = detail_page_soup.select_one(
        ".row-mobile-order-2:first-child div"
    ).text.strip()
    non_cyrillic_text = re.sub(r"[^\x00-\x7F]", "", description)

    return non_cyrillic_text


async def parse_single_vacancy(detail_url: str) -> Job:
    async with aiohttp.ClientSession() as session:
        response = await session.get(BASE_URL + detail_url)
        detail_page_soup = BeautifulSoup(await response.text(), "html.parser")

        salary = detail_page_soup.select_one(
            ".detail--title-wrapper span.public-salary-item"
        )
        salary = salary.text.strip() if salary else None

        experience = detail_page_soup.select_one(
            ".job-additional-info--item-text:-soup-contains('experience')"
        ).text.split()[0]
        if "No" in experience:
            experience = 0

        description = parse_job_description(detail_page_soup)

    return Job(
        name=detail_page_soup.select_one("h1").get_text(strip=True),
        salary=salary,
        experience=int(experience),
        views=int(detail_page_soup.select_one(".text-muted").text.split()[6]),
        applications=int(detail_page_soup.select_one(".text-muted").text.split()[-2]),
        description=description,
    )


async def get_one_page_jobs(soup: BeautifulSoup) -> [Job]:
    vacancies = soup.select(".job-list-item__link")
    tasks = [parse_single_vacancy(link["href"]) for link in vacancies]
    return await asyncio.gather(*tasks)


async def get_all_jobs() -> List[Job]:
    async with aiohttp.ClientSession() as session:
        response = await session.get(URL)
        first_page_soup = BeautifulSoup(await response.text(), "html.parser")

        pages_number = get_num_pages(first_page_soup)
        all_jobs = await get_one_page_jobs(first_page_soup)

        for page in tqdm(range(2, pages_number + 1)):
            next_page = await session.get(URL, params={"page": page})
            next_page_soup = BeautifulSoup(await next_page.text(), "html.parser")
            all_jobs.extend(await get_one_page_jobs(next_page_soup))

    return all_jobs


async def main():
    async with asyncio.TaskGroup() as tg:
        return await tg.create_task(get_all_jobs())


def write_jobs_to_csv(all_jobs: [Job]) -> None:
    with open(JOBS_OUTPUT_CSV, "w") as file:
        writer = csv.writer(file)
        writer.writerow(JOBS_FIELDS)
        writer.writerows([astuple(job) for job in all_jobs])


if __name__ == "__main__":
    start = time.perf_counter()

    result = asyncio.run(main())
    write_jobs_to_csv(result)

    duration = time.perf_counter() - start
    print(f"time:{duration}")
