from app.tools.calculator import calculator
from app.tools.datetime_tool import get_current_datetime
from app.tools.weather import get_weather
from app.tools.document_search import document_search


TOOLS = [
    calculator,
    get_current_datetime,
    get_weather,
    document_search,
]