import os
import requests

from dotenv import load_dotenv


load_dotenv()

SERPAPI_KEY = os.getenv(
    "SERPAPI_KEY",
    ""
).strip()


# =========================================================
# GENERIC GOOGLE SEARCH
# =========================================================

def google_search(
    query,
    max_results=6
):

    if not SERPAPI_KEY:

        return []

    try:

        params = {
            "engine": "google",
            "q": query,
            "api_key": SERPAPI_KEY,
            "num": max_results
        }

        response = requests.get(
            "https://serpapi.com/search.json",
            params=params,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        results = []

        for item in data.get(
            "organic_results",
            []
        )[:max_results]:

            title = item.get(
                "title",
                ""
            )

            snippet = item.get(
                "snippet",
                ""
            )

            link = item.get(
                "link",
                ""
            )

            if title or snippet:

                results.append({
                    "title": title,
                    "snippet": snippet,
                    "link": link
                })

        return results

    except Exception as error:

        print(
            f"Google search error: {error}"
        )

        return []


# =========================================================
# PRODUCT SEARCH
# =========================================================

def search_online_product(
    product_name,
    max_results=5
):

    query = (
        f"{product_name} official product "
        f"details ingredients usage"
    )

    return google_search(
        query,
        max_results
    )


def build_product_documents(
    product_name
):

    results = search_online_product(
        product_name
    )

    documents = []

    for item in results:

        document = f"""
Product: {product_name}

Title:
{item.get("title", "")}

Information:
{item.get("snippet", "")}

Source:
{item.get("link", "")}
"""

        documents.append(
            document.strip()
        )

    return documents


# =========================================================
# TNPSC BOOK SEARCH
# =========================================================

def search_tnpsc_books(
    query,
    max_results=8
):

    search_query = (
        f"TNPSC {query} "
        f"books study material syllabus "
        f"Group 1 Group 2 Group 4"
    )

    return google_search(
        search_query,
        max_results
    )


def build_tnpsc_documents(
    query
):

    results = search_tnpsc_books(
        query
    )

    documents = []

    for item in results:

        document = f"""
TNPSC Study Resource

Topic:
{query}

Title:
{item.get("title", "")}

Information:
{item.get("snippet", "")}

Source:
{item.get("link", "")}
"""

        documents.append(
            document.strip()
        )

    return documents


# =========================================================
# TNPSC OFFICIAL RESOURCE SEARCH
# =========================================================

def search_tnpsc_official(
    query,
    max_results=8
):

    search_query = (
        f"site:tnpsc.gov.in {query} "
        f"TNPSC syllabus question paper"
    )

    return google_search(
        search_query,
        max_results
    )


def build_tnpsc_official_documents(
    query
):

    results = search_tnpsc_official(
        query
    )

    documents = []

    for item in results:

        document = f"""
TNPSC OFFICIAL RESOURCE

Topic:
{query}

Title:
{item.get("title", "")}

Information:
{item.get("snippet", "")}

Official Source:
{item.get("link", "")}
"""

        documents.append(
            document.strip()
        )

    return documents