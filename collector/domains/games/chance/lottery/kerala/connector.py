"""
Kerala Lottery Connector
"""

from datetime import datetime
from typing import Optional, Dict, Any, Callable, Iterator
from urllib.parse import urljoin
import uuid

from collector.core.fetcher import HTTPFetcher
from collector.contracts.connector import Connector as BaseConnector
from collector.contracts.document import Document
from .history import OfficialHistoryResolver
from .legacy import (
    LEGACY_REPORT_URL,
    LegacyAddressRecord,
    LegacyAddressScanStalled,
    LegacyHistoryResolver,
    script_location,
)
from .parser import Parser


LegacyAddressProgress = Callable[[str, Optional[datetime], bool], None]


class Connector(BaseConnector):
    """
    A Connector for Kerala Lottery results.

    Modern results use the historical ``drawserial`` address space. Older official
    history rows use a separate legacy ``drawno`` namespace and are addressed to
    Collector explicitly as ``legacy:<drawno>``.

    No numeric ordering relationship is assumed between those namespaces.
    """

    RESULT_BASE = "http://result.keralalotteries.com/viewlotisresult.php"
    LEGACY_PREFIX = "legacy:"

    def __init__(self, **kwargs):
        self.fetcher = HTTPFetcher()
        self.parser = Parser()
        self.history_resolver = OfficialHistoryResolver()
        self.legacy_history_resolver = LegacyHistoryResolver()
        self._legacy_year_cache: dict[int, list[str]] = {}

    def retrieve(self, source: str) -> Document:
        """Retrieve a modern drawserial or an explicit legacy drawno source."""
        source_text = str(source)

        legacy_drawno = self._legacy_drawno(source_text)
        if legacy_drawno is not None:
            redirect_url = (
                f"{LEGACY_REPORT_URL}?drawno1={legacy_drawno}&drawno={legacy_drawno}"
            )
            redirect_doc = self.fetcher.retrieve(redirect_url)
            if redirect_doc.error or not redirect_doc.content:
                return redirect_doc

            location = script_location(bytes(redirect_doc.content))
            if not location:
                return redirect_doc

            pdf_url = urljoin(redirect_url, location)
            pdf_doc = self.fetcher.retrieve(pdf_url)
            pdf_doc.metadata["legacy_redirector_url"] = redirect_url
            pdf_doc.metadata["legacy_drawno"] = legacy_drawno
            return pdf_doc

        url = f"{self.RESULT_BASE}?drawserial={source_text}"
        try:
            source_id = int(source_text)
        except ValueError:
            # Preserve the existing fetch behaviour for unsupported/non-numeric
            # addresses; supports() remains the authority for address shape.
            return self.fetcher.retrieve(url)

        if not self.history_resolver.is_published_source(source_id):
            return Document(
                id=str(uuid.uuid4()),
                source_url=url,
                retrieved_at=datetime.now(),
                content=None,
                run_id=str(uuid.uuid4()),
                connector_id=self.__class__.__name__,
                metadata={"source_state": "not_published"},
            )

        return self.fetcher.retrieve(url)

    def parse(self, content: bytes) -> Optional[Dict[str, Any]]:
        """Parse Kerala result PDF content into the existing normalized contract."""
        result = self.parser.parse(content)
        if not result:
            return None

        return {
            "lottery_name": result.lottery_name,
            "draw_date": result.draw_date,
            "first_prize": result.first_prize,
            "first_prize_location": result.first_prize_location,
            "second_prize": result.second_prize,
            "second_prize_location": result.second_prize_location,
            "third_prize": result.third_prize,
            "third_prize_location": result.third_prize_location,
            "consolation_prizes": result.consolation_prizes,
            "prize_tiers": result.prize_tiers,
            "fourth_prize_numbers": result.fourth_prize_numbers,
            "fifth_prize_numbers": result.fifth_prize_numbers,
            "sixth_prize_numbers": result.sixth_prize_numbers,
            "seventh_prize_numbers": result.seventh_prize_numbers,
            "eighth_prize_numbers": result.eighth_prize_numbers,
            "ninth_prize_numbers": result.ninth_prize_numbers,
        }

    def previous_source(self, source: str) -> Optional[str]:
        """Return the nearest earlier published modern drawserial, if discoverable."""
        source_text = str(source)
        if self._legacy_drawno(source_text) is not None:
            return None

        try:
            before_source = int(source_text)
        except ValueError:
            return None

        previous = self.history_resolver.previous_source_id(before_source)
        return str(previous) if previous is not None else None

    def iter_legacy_address_records(
        self,
        start_drawno: int,
        *,
        max_consecutive_unusable: int = 100,
        progress: Optional[LegacyAddressProgress] = None,
    ) -> Iterator[LegacyAddressRecord]:
        """Yield verified legacy results while descending direct source addresses.

        ``drawno`` is treated only as an address to inspect, never as chronology.
        Each usable result is independently parsed and dated before it is yielded.

        Safety is progress-based: the scan continues while verified records keep
        appearing, and raises ``LegacyAddressScanStalled`` only after
        ``max_consecutive_unusable`` addresses produce no usable parsed result.
        A stall is unresolved source coverage, not proof that history ended.
        """
        if start_drawno < 1:
            return
        if max_consecutive_unusable < 1:
            raise ValueError("max_consecutive_unusable must be at least 1")

        consecutive_unusable = 0

        for drawno in range(int(start_drawno), 0, -1):
            source = f"{self.LEGACY_PREFIX}{drawno}"
            doc = self.retrieve(source)

            result = None
            if not doc.error and doc.content:
                result = self.parser.parse(bytes(doc.content))

            draw_date: Optional[datetime] = None
            lottery_name = ""
            if result and result.draw_date and result.draw_date != "Unknown":
                try:
                    draw_date = datetime.strptime(result.draw_date, "%d/%m/%Y")
                except ValueError:
                    draw_date = None
                lottery_name = " ".join(str(result.lottery_name or "").split())

            usable = draw_date is not None and bool(lottery_name)
            if progress is not None:
                progress(source, draw_date, usable)

            if not usable:
                consecutive_unusable += 1
                if consecutive_unusable >= max_consecutive_unusable:
                    raise LegacyAddressScanStalled(
                        last_drawno=drawno,
                        consecutive_unusable=consecutive_unusable,
                    )
                continue

            consecutive_unusable = 0
            assert draw_date is not None
            yield LegacyAddressRecord(
                drawno=drawno,
                draw_date=draw_date.date(),
                lottery_name=lottery_name,
            )

    def resolve_legacy_address_continuation(
        self,
        stalled_drawno: int,
        *,
        max_probe: int = 100,
        progress: Optional[LegacyAddressProgress] = None,
    ) -> Optional[LegacyAddressRecord]:
        """Find the first verified legacy record below an unresolved scan stall.

        This is a bounded continuation resolver, not a chronology resolver. It
        inspects at most ``max_probe`` lower direct addresses and returns the first
        independently parsed result. Returning a record proves only that the
        transport continues below the stall; returning ``None`` leaves coverage
        unresolved. Neither outcome proves that historical events are contiguous.
        """
        if max_probe < 1:
            raise ValueError("max_probe must be at least 1")
        if stalled_drawno <= 1:
            return None

        lowest_drawno = max(1, int(stalled_drawno) - int(max_probe))

        for drawno in range(int(stalled_drawno) - 1, lowest_drawno - 1, -1):
            source = f"{self.LEGACY_PREFIX}{drawno}"
            doc = self.retrieve(source)

            result = None
            if not doc.error and doc.content:
                result = self.parser.parse(bytes(doc.content))

            draw_date: Optional[datetime] = None
            lottery_name = ""
            if result and result.draw_date and result.draw_date != "Unknown":
                try:
                    draw_date = datetime.strptime(result.draw_date, "%d/%m/%Y")
                except ValueError:
                    draw_date = None
                lottery_name = " ".join(str(result.lottery_name or "").split())

            usable = draw_date is not None and bool(lottery_name)
            if progress is not None:
                progress(source, draw_date, usable)

            if not usable:
                continue

            assert draw_date is not None
            return LegacyAddressRecord(
                drawno=drawno,
                draw_date=draw_date.date(),
                lottery_name=lottery_name,
            )

        return None

    def legacy_sources_for_year(self, year: int) -> list[str]:
        """Discover official legacy sources whose parsed held date falls in ``year``.

        Discovery walks each official legacy lottery family in its own published
        family order. It never compares drawno values across families. Every source
        is validated through the same retrieve/parse path used by Collector.
        """
        if year in self._legacy_year_cache:
            return list(self._legacy_year_cache[year])

        discovered: list[tuple[datetime, str]] = []
        seen_sources: set[str] = set()

        for family in self.legacy_history_resolver.families():
            for item in family.sources:
                source_text = item.source
                doc = self.retrieve(source_text)

                if doc.error or not doc.content:
                    raise RuntimeError(
                        f"Legacy source {source_text} could not be retrieved: {doc.error}"
                    )

                result = self.parser.parse(bytes(doc.content))
                if not result or not result.draw_date or result.draw_date == "Unknown":
                    raise RuntimeError(
                        f"Legacy source {source_text} has no usable held date."
                    )

                try:
                    draw_date = datetime.strptime(result.draw_date, "%d/%m/%Y")
                except ValueError as exc:
                    raise RuntimeError(
                        f"Legacy source {source_text} has invalid held date {result.draw_date!r}."
                    ) from exc

                if draw_date.year > year:
                    continue

                if draw_date.year == year:
                    if source_text not in seen_sources:
                        seen_sources.add(source_text)
                        discovered.append((draw_date, source_text))
                    continue

                break

        ordered = [source for _date, source in sorted(discovered)]
        self._legacy_year_cache[year] = ordered
        return list(ordered)

    def supports(self, source: str) -> bool:
        """Check whether the connector supports this explicit source address."""
        source_text = str(source)
        if self._legacy_drawno(source_text) is not None:
            return True

        try:
            int(source_text)
            return True
        except ValueError:
            return False

    @classmethod
    def _legacy_drawno(cls, source: str) -> Optional[int]:
        if not source.startswith(cls.LEGACY_PREFIX):
            return None

        raw = source[len(cls.LEGACY_PREFIX) :]
        if not raw.isdigit():
            return None
        return int(raw)
