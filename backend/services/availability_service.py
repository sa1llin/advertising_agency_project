from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.models.advertising_space_model import AdvertisingSpace
from backend.models.order_model import Order
from backend.models.order_segment_model import OrderSegment
from backend.schemas.order_schema import OrderSegmentInput

LED_WORK_START_HOUR = 5
LED_WORK_END_HOUR = 23
LED_DAILY_CAPACITY_SECONDS = (LED_WORK_END_HOUR - LED_WORK_START_HOUR) * 60 * 60
LED_BLOCK_SECONDS = 600
LED_BLOCKS_PER_DAY = LED_DAILY_CAPACITY_SECONDS // LED_BLOCK_SECONDS


@dataclass(frozen=True)
class Allocation:
    space_id: int
    period_start: date
    period_end: date
    daily_seconds: int
    order_number: str


def validate_space_availability(
    db: Session,
    order_type: str,
    segments: list[OrderSegmentInput],
    *,
    exclude_order_id: int | None = None,
) -> None:
    if order_type not in ("billboard", "led") or not segments:
        return

    relevant = [
        segment
        for segment in segments
        if segment.advertising_space_id is not None
        and segment.period_start is not None
        and segment.period_end is not None
    ]
    if not relevant:
        return

    spaces = _load_spaces(
        db,
        {int(segment.advertising_space_id) for segment in relevant},
        order_type,
    )
    existing = _load_allocations(
        db,
        set(spaces),
        exclude_order_id=exclude_order_id,
    )
    planned: list[Allocation] = []

    for segment in relevant:
        space_id = int(segment.advertising_space_id)
        space = spaces[space_id]
        candidate = Allocation(
            space_id=space_id,
            period_start=segment.period_start,
            period_end=segment.period_end,
            daily_seconds=_segment_daily_seconds(order_type, segment),
            order_number="поточне замовлення",
        )
        same_space = [
            allocation
            for allocation in [*existing, *planned]
            if allocation.space_id == space_id
        ]
        if order_type == "billboard":
            _validate_billboard(space, candidate, same_space)
        else:
            _validate_led(space, candidate, same_space, segment)
        planned.append(candidate)


def _load_spaces(
    db: Session,
    space_ids: set[int],
    expected_type: str,
) -> dict[int, AdvertisingSpace]:
    spaces = (
        db.query(AdvertisingSpace)
        .filter(
            AdvertisingSpace.id.in_(space_ids),
            AdvertisingSpace.space_type == expected_type,
            AdvertisingSpace.is_active.is_(True),
        )
        .order_by(AdvertisingSpace.id)
        .with_for_update()
        .all()
    )
    result = {space.id: space for space in spaces}
    missing = sorted(space_ids - set(result))
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Обрану рекламну площину не знайдено, вона неактивна "
                "або має інший тип."
            ),
        )
    return result


def _load_allocations(
    db: Session,
    space_ids: set[int],
    *,
    exclude_order_id: int | None,
) -> list[Allocation]:
    query = (
        db.query(OrderSegment, Order)
        .join(Order, Order.id == OrderSegment.order_id)
        .filter(
            OrderSegment.advertising_space_id.in_(space_ids),
            OrderSegment.period_start.is_not(None),
            OrderSegment.period_end.is_not(None),
            Order.status != "cancelled",
        )
    )
    if exclude_order_id is not None:
        query = query.filter(Order.id != exclude_order_id)

    allocations: list[Allocation] = []
    for segment, order in query.all():
        allocations.append(
            Allocation(
                space_id=segment.advertising_space_id,
                period_start=segment.period_start,
                period_end=segment.period_end,
                daily_seconds=(
                    int(segment.video_seconds or 0)
                    * int(segment.impressions_per_day or 0)
                ),
                order_number=order.order_number,
            )
        )
    return allocations


def _validate_billboard(
    space: AdvertisingSpace,
    candidate: Allocation,
    allocations: list[Allocation],
) -> None:
    conflict = next(
        (allocation for allocation in allocations if _overlaps(candidate, allocation)),
        None,
    )
    if conflict is None:
        return

    available_from = conflict.period_end + timedelta(days=1)
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=(
            f"Білборд «{space.location}» уже зайнятий замовленням "
            f"{conflict.order_number} у період "
            f"{_date_text(conflict.period_start)}–"
            f"{_date_text(conflict.period_end)}. "
            f"Він стане доступним з {_date_text(available_from)}. "
            "Оберіть іншу площину або період без перетину."
        ),
    )


def _validate_led(
    space: AdvertisingSpace,
    candidate: Allocation,
    allocations: list[Allocation],
    segment: OrderSegmentInput,
) -> None:
    conflict = _maximum_usage_interval(candidate, allocations)
    if conflict is None:
        return
    conflict_start, conflict_end, used_seconds = conflict
    requested_seconds = candidate.daily_seconds
    if used_seconds + requested_seconds <= LED_DAILY_CAPACITY_SECONDS:
        return

    available_seconds = max(LED_DAILY_CAPACITY_SECONDS - used_seconds, 0)
    video_seconds = int(segment.video_seconds or 0)
    optimal_impressions = available_seconds // video_seconds if video_seconds > 0 else 0
    used_percent = _percent(used_seconds)
    requested_percent = _percent(requested_seconds)
    total_percent = _percent(used_seconds + requested_seconds)
    optimal_percent = _percent(optimal_impressions * video_seconds)
    period = (
        _date_text(conflict_start)
        if conflict_start == conflict_end
        else f"{_date_text(conflict_start)}–{_date_text(conflict_end)}"
    )

    recommendation = (
        f"Для ролика {video_seconds} с оптимально встановити не більше "
        f"{optimal_impressions} показів на день "
        f"({optimal_impressions * video_seconds} с/день, "
        f"{optimal_percent:.2f}%)."
        if optimal_impressions > 0
        else "У цей період вільного рекламного часу немає."
    )
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=(
            f"LED-екран «{space.location}» перевантажений у період {period}. "
            f"Поточне навантаження: {used_seconds} з "
            f"{LED_DAILY_CAPACITY_SECONDS} с/день ({used_percent:.2f}%). "
            f"Новий запит: {requested_seconds} с/день "
            f"({requested_percent:.2f}%), разом {total_percent:.2f}%. "
            f"Екран працює {LED_WORK_END_HOUR - LED_WORK_START_HOUR} годин "
            f"і має {LED_BLOCKS_PER_DAY} блоків по {LED_BLOCK_SECONDS} с. "
            f"{recommendation}"
        ),
    )


def _maximum_usage_interval(
    candidate: Allocation,
    allocations: list[Allocation],
) -> tuple[date, date, int] | None:
    overlapping = [
        allocation for allocation in allocations if _overlaps(candidate, allocation)
    ]
    if not overlapping:
        return None

    end_marker = candidate.period_end + timedelta(days=1)
    points = {candidate.period_start, end_marker}
    for allocation in overlapping:
        points.add(max(candidate.period_start, allocation.period_start))
        points.add(min(candidate.period_end, allocation.period_end) + timedelta(days=1))
    ordered = sorted(points)
    intervals: list[tuple[date, date, int]] = []
    for index in range(len(ordered) - 1):
        start = ordered[index]
        end = ordered[index + 1] - timedelta(days=1)
        if start > end:
            continue
        usage = sum(
            allocation.daily_seconds
            for allocation in overlapping
            if allocation.period_start <= start <= allocation.period_end
        )
        intervals.append((start, end, usage))
    return max(intervals, key=lambda item: item[2], default=None)


def _segment_daily_seconds(
    order_type: str,
    segment: OrderSegmentInput,
) -> int:
    if order_type != "led":
        return 0
    return int(segment.video_seconds or 0) * int(segment.impressions_per_day or 0)


def _overlaps(first: Allocation, second: Allocation) -> bool:
    return (
        first.period_end >= second.period_start
        and first.period_start <= second.period_end
    )


def _percent(seconds: int) -> float:
    return seconds * 100 / LED_DAILY_CAPACITY_SECONDS


def _date_text(value: date) -> str:
    return value.strftime("%d.%m.%Y")
