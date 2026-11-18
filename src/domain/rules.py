from zoneinfo import ZoneInfo

TIMEZONE_NAME = "Europe/Moscow"
MSK = ZoneInfo(TIMEZONE_NAME)
ADULT_AGE = 18
LICENSE_KEY_PREFIX = "drl_"
LICENSE_KEY_LENGTH = 36
DAILY_LICENSE_LIMIT = 3
RENEWAL_WINDOW_DAYS = 30
REPLACED_REASON = "заменена новой лицензией"
PHONE_PATTERN = r"^\+7\d{10}$"
PHONE_LENGTH = 12
FULL_NAME_MAX_LENGTH = 255
EMAIL_MAX_LENGTH = 255
SKU_MAX_LENGTH = 64
NAME_MAX_LENGTH = 200
MANUFACTURER_MAX_LENGTH = 100
DRONE_EDITABLE_FIELDS = frozenset(
    {
        "sku",
        "name",
        "manufacturer",
        "purpose",
        "rank",
        "weight_g",
        "max_flight_time_min",
        "max_range_m",
        "has_camera",
        "price",
        "status",
    }
)
PART_EDITABLE_FIELDS = frozenset({"name", "purpose", "price", "drone_id"})
