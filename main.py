import itertools
from datetime import time
from typing import Iterable

from pydantic import BaseModel
from pydantic.class_validators import validator
from pydantic.tools import parse_obj_as


def get_time_total_minutes(t: time) -> int:
    return (t.hour * 60) + t.minute


def minutes_to_time(m: int) -> time:
    return time(hour=m // 60, minute=m % 60)


class TimeInterval(BaseModel):
    start: time
    stop: time
    start_total_minutes: int = None
    stop_total_minutes: int = None

    @validator("start_total_minutes", always=True)
    def calculate_start_total_minutes(cls, v, values, **kwargs) -> int:
        return get_time_total_minutes(values['start'])

    @validator("stop_total_minutes", always=True)
    def calculate_stop_total_minutes(cls, v, values, **kwargs) -> int:
        return get_time_total_minutes(values['stop'])


def batch(iterable, n=1):
    """Аналог itertools.batched, но отсекает неполный последний батч"""
    l = len(iterable)
    for ndx in range(0, l, n):
        b = iterable[ndx:min(ndx + n, l)]
        if len(b) == n:
            yield b


def get_business_hours(busy_hours: Iterable[TimeInterval],
                       work_day: TimeInterval, duration_min: int):
    free_hours = [work_day.start_total_minutes]

    for b in sorted(busy_hours, key=lambda h: h.start_total_minutes):
        free_hours.extend((b.start_total_minutes, b.stop_total_minutes))
    free_hours.append(work_day.stop_total_minutes)

    result = []
    # нарезав рабочее время, получаем свободные окна
    free_hours = batch(free_hours, 2)
    for free_time_start, free_time_stop in free_hours:
        # нарезаем свободное окно на периоды времени
        # пришлось к range добавить +1 чтобы было "включительно"
        free_window = range(free_time_start, free_time_stop + 1, duration_min)

        pairs = itertools.pairwise(free_window)
        for start_half_hour_period, stop_half_hour_period in pairs:
            appointment = TimeInterval(
                start=minutes_to_time(start_half_hour_period),
                stop=minutes_to_time(stop_half_hour_period))
            result.append(appointment)
    return result


if __name__ == "__main__":
    busy = [
        {"start": "10:30", "stop": "10:50"},
        {"start": "18:40", "stop": "18:50"},
        {"start": "14:40", "stop": "15:50"},
        {"start": "16:40", "stop": "17:20"},
        {"start": "20:05", "stop": "20:20"},
    ]

    bh = get_business_hours(work_day=TimeInterval(start="09:00", stop="21:00"),
                            busy_hours=parse_obj_as(list[TimeInterval], busy),
                            duration_min=30)
    print(bh)
