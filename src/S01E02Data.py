"""Dane do zadań z S01E02"""

people = [
    {"name": "Cezary", "surname": "Żurek", "born": 1987},
    {"name": "Jacek", "surname": "Nowak", "born": 1991},
    {"name": "Oskar", "surname": "Sieradzki", "born": 1993},
    {"name": "Wojciech", "surname": "Bielik", "born": 1986},
    {"name": "Wacław", "surname": "Jasiński", "born": 1986}
]


people_full_data = [
    {"name": "Cezary", "surname": "Żurek", "gender": "M", "born": 1987, "city": "Grudziądz", "tags": ["transport"]},
    {"name": "Jacek", "surname": "Nowak", "gender": "M", "born": 1991, "city": "Grudziądz", "tags": ["transport"]},
    {"name": "Oskar", "surname": "Sieradzki", "gender": "M", "born": 1993, "city": "Grudziądz", "tags": ["transport"]},
    {"name": "Wojciech", "surname": "Bielik", "gender": "M", "born": 1986, "city": "Grudziądz", "tags": ["transport"]},
    {"name": "Wacław", "surname": "Jasiński", "gender": "M", "born": 1986, "city": "Grudziądz", "tags": ["transport"]}
]

power_plants = {
    "Zabrze": {
        "is_active": True,
        "power": "35 MW",
        "code": "PWR3847PL"
    },
    "Piotrków Trybunalski": {
        "is_active": True,
        "power": "28 MW",
        "code": "PWR5921PL"
    },
    "Grudziądz": {
        "is_active": True,
        "power": "1138 MW",
        "code": "PWR7264PL"
    },
    "Tczew": {
        "is_active": True,
        "power": "31 MW",
        "code": "PWR1593PL"
    },
    "Radom": {
        "is_active": True,
        "power": "38 MW",
        "code": "PWR8406PL"
    },
    "Chelmno": {
        "is_active": True,
        "power": "128 MW",
        "code": "PWR2758PL"
    },
    "Żarnowiec": {
        "is_active": False,
        "power": "0 MW",
        "code": "PWR6132PL"
    }
}