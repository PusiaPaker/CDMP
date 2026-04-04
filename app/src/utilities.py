#
#
#
import re
from datetime import date, datetime, time

from dateutil.parser import parse as parse_date

# we need this to support different values from the spreadsheet input
# for the frequency
EXPENSE_FREQUENCY_ALIASES = {
    "one time": "one_time",
    "one-time": "one_time",
    "one_time": "one_time",
    "onetime": "one_time",
    "monthly": "monthly",
    "month": "monthly",
    "annual": "annual",
    "annually": "annual",
    "yearly": "annual",
}


def normalize_role_to_level(role_name: str | None) -> int:
    '''
    People spreadsheet "Role" column values need to be mapped onto a level number
    to build the organizational chart hierarchy properly
    '''
    if not role_name:
        return 5

    name = re.sub(r"[^a-z0-9]+", " ", role_name.lower()).strip()

    role_keywords = [
        (0, [
            "chief", "ceo", "cfo", "coo", "cio", "cto", "cmo", "chro", "cao",
            "president", "founder", "co founder", "owner", "partner",
            "managing partner", "board", "chair", "chairman", "chairwoman",
            "executive sponsor"
        ]),
        (1, [
            "evp", "svp", "vp", "vice president",
            "director", "senior director", "executive director",
            "managing director", "head of", "general manager"
        ]),
        (2, [
            "senior manager", "sr manager", "manager", "supervisor",
            "project manager", "program manager", "product manager",
            "portfolio manager", "delivery manager", "engagement manager"
        ]),
        (3, [
            "team lead", "lead", "practice lead", "chapter lead",
            "lead analyst", "lead engineer", "lead consultant",
            "lead developer", "lead architect"
        ]),
        (4, [
            "principal", "staff", "architect", "advisor",
            "senior consultant", "senior analyst", "senior engineer",
            "senior developer", "senior specialist",
            "subject matter expert", "sme"
        ]),
        (5, [
            "consultant", "analyst", "associate", "coordinator",
            "engineer", "developer", "specialist", "administrator",
            "representative", "technician", "operator",
            "assistant", "intern", "frontline"
        ]),
    ]

    for level, keywords in role_keywords:
        if any(keyword in name for keyword in keywords):
            return level

    return 5


def parse_import_date(value, *, as_datetime=False):
    '''
    Parse flexible date inputs used by spreadsheet imports.
    Supports common formats like YYYY-MM-DD, M/D/YYYY, and month-name dates,

    this uses the python-dateutil library parse function to be able
    to extract date info in any format (it's easier than trying to account
    for everything manually)
    '''
    if value is None:
        raise ValueError("Missing date")

    if isinstance(value, datetime):
        return value if as_datetime else value.date()

    if isinstance(value, date):
        return datetime.combine(value, time.min) if as_datetime else value

    text = str(value).strip()
    if text == "":
        raise ValueError("Missing date")

    parsed = parse_date(text, dayfirst=False, yearfirst=False)
    return parsed if as_datetime else parsed.date()


def normalize_expense_frequency(value: str) -> str:
    '''
    Normalize supported expense frequency values to the canonical DB values.
    '''
    normalized = EXPENSE_FREQUENCY_ALIASES.get(str(value).strip().lower())
    if not normalized:
        raise ValueError("Invalid expense frequency")

    return normalized
