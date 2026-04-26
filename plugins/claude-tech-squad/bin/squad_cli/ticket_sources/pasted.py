from __future__ import annotations

from squad_cli.ticket_sources.base import TicketSourceAdapter


class PastedTicketAdapter(TicketSourceAdapter):
    source = "pasted"
