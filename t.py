
import pytz

from dateutil import parser

TZ = pytz.timezone("America/New_York")

date = parser.parse("2024-03-21T10:05:00Z")

date = date.astimezone(tz=TZ)

print(date)