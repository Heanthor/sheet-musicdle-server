import requests


def get_page_text(url: str) -> str:
    try_page = requests.get(url)
    print("Got response.")
    status = try_page.status_code
    if status == 404:
        raise Exception("Page not found: " + url)

    if status != 200:
        raise Exception(f"Status ({status}) loading page: {url}")

    return try_page.text
