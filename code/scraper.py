import requests
from bs4 import BeautifulSoup
from code.iso_country_codes import CC
import dataclasses
import json


@dataclasses.dataclass
class Result:
    event_name: str
    bib_number: int
    gender: str
    country: str
    name: str
    time: str
    category: str


EVENTS = {
    1: "Marathon",
    8: "Wheelchair Marathon",
    2: "Half Marathon",
    6: "Wheelchair Half Marathon",
    3: "10km",
    9: "Wheelchair 10km",
    4: "5km",
    5: "2km",
}


def fetch_results(event_id: int, event_name: str, page_number: int) -> list[Result]:
    print(f"Requesting page {page_number}")

    results: list[Result] = []

    url = f"https://results.sportseventservices.com.au/results.aspx?CId=16287&RId=6373&EId={event_id}&dt=0&PageNo={page_number}"
    response = requests.get(url)
    response.raise_for_status()

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        table_div = soup.find("div", id="ctl00_Content_Main_divGrid")

        # If the table is None, then we're requesting a page that doesn't
        # exist. Just return a blank set of results.
        if table_div is None:
            return []

        table = table_div.find("table")
        rows = table.find_all("tr")
        # Skip the first row because it's headings.
        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            (
                _,
                race_number,
                position,
                gender,
                gender_position,
                _,
                country_image_cell,
                name,
                _,
                time_cell,
                category,
                _,
            ) = cells

            # Try to get the country code. Some are just blank...
            try:
                country_code = (
                    country_image_cell.contents[0]["src"].split("/")[-1].split(".")[0]
                )
                country = CC[country_code]
            except KeyError:
                country = "Unknown"

            results.append(
                Result(
                    event_name=event_name,
                    bib_number=int(race_number.text),
                    gender=gender.text,
                    country=country,
                    name=name.text,
                    time=time_cell.text,
                    category=category.text,
                )
            )

    return results


def get_results_for_event(event_id: int, event_name: str) -> list[Result]:
    print(f"Getting results for event: {event_name}")
    event_results: list[Result] = []

    page = 1
    while True:
        # Fetch the first page
        page_results = fetch_results(event_id, event_name, page)
        if page_results:
            event_results.extend(page_results)
        else:
            break

        page += 1

    return event_results


def main() -> None:
    results: list[Result] = []

    for event_id, event_name in EVENTS.items():
        results.extend(get_results_for_event(event_id, event_name))

    list_of_results = list(map(dataclasses.asdict, results))

    with open("results.json", "w") as fp:
        json.dump(list_of_results, fp)


if __name__ == "__main__":
    main()
