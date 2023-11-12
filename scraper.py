import csv
import time
from dataclasses import dataclass, fields, astuple

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://djinni.co"
URL = "https://djinni.co/jobs/?primary_keyword=Python"
JOBS_OUTPUT_CSV = "jobs.csv"


@dataclass
class Job:
    name: str
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


def parse_job_details(detail_url: str) -> str:
    response = requests.get(BASE_URL + detail_url).content
    detail_page_soup = BeautifulSoup(response, "html.parser")

    description = detail_page_soup.select_one(".row-mobile-order-2").text.strip()

    return description


def parse_single_vacancy(vacancies: BeautifulSoup) -> Job:
    experience = vacancies.select_one("span:-soup-contains('experience')").text.split()[
        1
    ]
    if "No" in experience:
        experience = 0

    vacancy_detail = vacancies.select_one(".job-list-item__link")["href"]
    description = parse_job_details(vacancy_detail)

    return Job(
        name=vacancies.select_one(".job-list-item__link").text.strip(),
        experience=int(experience),
        views=int(vacancies.select_one(".text-muted").text.split()[-2]),
        applications=int(vacancies.select_one(".text-muted").text.split()[-1]),
        description=description,
    )


def get_one_page_jobs(soup: BeautifulSoup) -> [Job]:
    vacancies = soup.select(".list-jobs__item")
    return [parse_single_vacancy(vacancy) for vacancy in vacancies]


def get_all_jobs() -> [Job]:
    response = requests.get(URL).content
    first_page_soup = BeautifulSoup(response, "html.parser")

    num_pages = get_num_pages(first_page_soup)
    all_jobs_list = get_one_page_jobs(first_page_soup)

    for page_num in range(2, num_pages + 1):
        page_response = requests.get(URL, params={"page": page_num}).content
        page_soup = BeautifulSoup(page_response, "html.parser")
        all_jobs_list.extend(get_one_page_jobs(page_soup))

    return all_jobs_list


def write_jobs_to_csv(all_jobs: [Job]) -> None:
    with open(JOBS_OUTPUT_CSV, "w") as file:
        writer = csv.writer(file)
        writer.writerow(JOBS_FIELDS)
        writer.writerows([astuple(job) for job in all_jobs])


if __name__ == "__main__":
    start = time.perf_counter()
    jobs = get_all_jobs()
    write_jobs_to_csv(jobs)
    duration = time.perf_counter() - start
    print(f"time:{duration}")
