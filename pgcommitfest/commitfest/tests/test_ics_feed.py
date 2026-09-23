"""
Tests for the /commitfests.ics calendar feed.
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, cast

import pytest
from icalendar import Calendar, Event

if TYPE_CHECKING:
    from pgcommitfest.commitfest.models import CommitFest

pytestmark = pytest.mark.django_db


def _get_calendar(client) -> Calendar:
    response = client.get("/commitfests.ics")
    assert response.status_code == 200
    assert response["Content-Type"] == "text/calendar; charset=utf-8"
    return Calendar.from_ical(response.content)


def _get_events(calendar: Calendar) -> list[Event]:
    return cast("list[Event]", calendar.walk("VEVENT"))


def test_commitfests_ics_empty(client):
    """
    With no commitfests, we still get a valid, empty calendar.
    """
    calendar = _get_calendar(client)

    assert len(_get_events(calendar)) == 0


def test_commitfests_ics_contains_all_commitfests(client, commitfests: dict[str, CommitFest]):
    """
    Every commitfest, regardless of status, shows up as a VEVENT with the right
    dates, DTEND being the day after enddate (exclusive).
    """
    calendar = _get_calendar(client)

    events = _get_events(calendar)
    assert len(events) == len(commitfests)

    events_by_uid = {cast("str", event.uid): event for event in events}

    for cf in commitfests.values():
        event = events_by_uid[f"commitfest-{cf.name}@commitfest.postgresql.org"]
        assert event.summary == f"Commitfest {cf.name}"
        assert event.url == f"https://commitfest.postgresql.org/{cf.pk}/"
        assert event.description == f"Status: {cf.statusstring}"
        assert event.start == cf.startdate
        assert event.end == cf.enddate + timedelta(days=1)
