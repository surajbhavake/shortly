
import pytest


async def test_health(client):
    """Check that the health endpoint is working."""
    r = await client.get("/health")

    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


async def test_create_link(client):
    """Check that a short link can be created."""
    r = await client.post(
        "/links",
        json={"url": "https://example.com/long/path"}
    )

    assert r.status_code == 201

    data = r.json()

    assert data["slug"]
    assert data["url"] == "https://example.com/long/path"
    assert data["short_url"].endswith(f"/{data['slug']}")
    assert data["clicks"] == 0
    assert data["created_at"] is not None


async def test_redirect_increments_clicks(client):
    """Check redirect functionality and click counting."""

    # Create a short link
    response = await client.post(
        "/links",
        json={"url": "https://example.com"}
    )

    slug = response.json()["slug"]

    # First redirect
    r = await client.get(
        f"/{slug}",
        follow_redirects=False
    )

    assert r.status_code == 302
    assert r.headers["location"] == "https://example.com/"

    # Check first click
    r = await client.get(f"/links/{slug}/stats")
    assert r.status_code == 200
    assert r.json()["clicks"] == 1

    # Second redirect
    await client.get(
        f"/{slug}",
        follow_redirects=False
    )

    # Check second click
    r = await client.get(f"/links/{slug}/stats")
    assert r.json()["clicks"] == 2


async def test_custom_slug(client):
    """Check that users can create links with custom slugs."""

    r = await client.post(
        "/links",
        json={
            "url": "https://example.com/",
            "custom_slug": "mylink"
        }
    )

    assert r.status_code == 201

    data = r.json()

    assert data["slug"] == "mylink"
    assert data["url"] == "https://example.com/"


async def test_custom_slug_redirect(client):
    """Check that a custom slug redirects to its original URL."""

    await client.post(
        "/links",
        json={
            "url": "https://example.com/",
            "custom_slug": "customlink"
        }
    )

    r = await client.get(
        "/customlink",
        follow_redirects=False
    )

    assert r.status_code == 302
    assert r.headers["location"] == "https://example.com/"


async def test_custom_slug_conflict(client):
    """Check that duplicate custom slugs are rejected."""

    # First link
    first = await client.post(
        "/links",
        json={
            "url": "https://a.com",
            "custom_slug": "taken"
        }
    )

    assert first.status_code == 201

    # Second link with the same slug
    second = await client.post(
        "/links",
        json={
            "url": "https://b.com",
            "custom_slug": "taken"
        }
    )

    assert second.status_code == 409


async def test_unknown_slug_404(client):
    """Check that an unknown slug returns 404."""

    r = await client.get(
        "/doesnotexist",
        follow_redirects=False
    )

    assert r.status_code == 404


async def test_invalid_url_422(client):
    """Check that invalid URLs are rejected."""

    r = await client.post(
        "/links",
        json={"url": "not-a-url"}
    )

    assert r.status_code == 422


async def test_list_links(client):
    """Check that all created links are returned."""

    # Create two links
    first = await client.post(
        "/links",
        json={"url": "https://a.com"}
    )

    second = await client.post(
        "/links",
        json={"url": "https://b.com"}
    )

    assert first.status_code == 201
    assert second.status_code == 201

    # Retrieve links
    r = await client.get("/links")

    assert r.status_code == 200

    data = r.json()

    assert len(data) == 2

    slugs = [item["slug"] for item in data]

    assert first.json()["slug"] in slugs
    assert second.json()["slug"] in slugs
