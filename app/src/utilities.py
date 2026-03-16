#
#
#
import re

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