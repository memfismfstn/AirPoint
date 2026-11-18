from enum import StrEnum


class FlightRank(StrEnum):
    """Лётный ранг: общая шкала для дронов и лицензий"""

    ROOKIE = "ROOKIE"
    PILOT = "PILOT"
    PRO = "PRO"
    ACE = "ACE"

    @property
    def level(self) -> int:
        """Числовой уровень ранга: ROOKIE=1 ... ACE=4"""
        return _RANK_LEVELS[self]


_RANK_LEVELS: dict[FlightRank, int] = {
    FlightRank.ROOKIE: 1,
    FlightRank.PILOT: 2,
    FlightRank.PRO: 3,
    FlightRank.ACE: 4,
}
