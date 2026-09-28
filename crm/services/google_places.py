import requests

from django.conf import settings


GOOGLE_PLACES_SEARCH_URL = (
    "https://places.googleapis.com/v1/places:searchText"
)


def search_businesses(query):
    """
    Search Google Places for businesses matching the supplied query.

    Returns a simplified list of business results that ConnectCRM can use
    when creating a company record.
    """

    api_key = settings.GOOGLE_PLACES_API_KEY

    if not api_key:
        raise RuntimeError(
            "GOOGLE_PLACES_API_KEY is not configured."
        )

    if not query or not query.strip():
        return []

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": (
            "places.id,"
            "places.displayName,"
            "places.formattedAddress,"
            "places.nationalPhoneNumber,"
            "places.websiteUri,"
            "places.primaryType,"
            "places.primaryTypeDisplayName"
        ),
    }

    payload = {
        "textQuery": query.strip(),
        "pageSize": 5,
    }

    response = requests.post(
        GOOGLE_PLACES_SEARCH_URL,
        headers=headers,
        json=payload,
        timeout=10,
    )

    response.raise_for_status()

    data = response.json()

    results = []

    for place in data.get("places", []):
        display_name = place.get("displayName", {})

        results.append(
            {
                "id": place.get("id", ""),
                "name": display_name.get("text", ""),
                "address": place.get(
                    "formattedAddress",
                    "",
                ),
                "phone": place.get(
                    "nationalPhoneNumber",
                    "",
                ),
                "website": place.get(
                    "websiteUri",
                    "",
                ),
                "industry": place.get(
                    "primaryTypeDisplayName",
                    {},
                ).get("text", ""),
                "type": place.get(
                    "primaryType",
                    "",
                ),
            }
        )

    return results