"""
Multi-tenant config — 5 kapperszaken.
Elke zaak heeft eigen naam, adres, diensten en openingstijden.
"""

BUSINESSES = {
    "kapsalon-knal": {
        "name": "Kapsalon Knal",
        "address": "Kalverstraat 12, 1012 AA Amsterdam",
        "phone": "+31201234567",
        "ai_name": "Emma",
        "owner": "Lisa van den Berg",
        "services": [
            {"name": "knippen", "price": 25, "duration_min": 30},
            {"name": "verven", "price": 60, "duration_min": 60},
            {"name": "föhnen", "price": 20, "duration_min": 15},
            {"name": "baard trimmen", "price": 15, "duration_min": 20},
        ],
        "stylists": ["Lisa", "Kim", "Daan"],
        "opening_hours": {
            "monday":    {"open": "09:00", "close": "18:00"},
            "tuesday":   {"open": "09:00", "close": "18:00"},
            "wednesday": {"open": "09:00", "close": "18:00"},
            "thursday":  {"open": "09:00", "close": "20:00"},
            "friday":    {"open": "09:00", "close": "18:00"},
            "saturday":  {"open": "09:00", "close": "17:00"},
            "sunday":    None,
        },
        "slot_interval_min": 30,
    },
    "scissor-sisters": {
        "name": "Scissor Sisters",
        "address": "Witte de Withstraat 8, 3012 BP Rotterdam",
        "phone": "+31101234567",
        "ai_name": "Sanne",
        "owner": "Mark Jansen",
        "services": [
            {"name": "knippen", "price": 28, "duration_min": 30},
            {"name": "verven", "price": 65, "duration_min": 60},
            {"name": "föhnen", "price": 22, "duration_min": 15},
            {"name": "baard trimmen", "price": 18, "duration_min": 20},
        ],
        "stylists": ["Mark", "Demi", "Sam"],
        "opening_hours": {
            "monday":    None,
            "tuesday":   {"open": "10:00", "close": "18:00"},
            "wednesday": {"open": "10:00", "close": "18:00"},
            "thursday":  {"open": "10:00", "close": "20:00"},
            "friday":    {"open": "10:00", "close": "18:00"},
            "saturday":  {"open": "10:00", "close": "17:00"},
            "sunday":    {"open": "11:00", "close": "16:00"},
        },
        "slot_interval_min": 30,
    },
    "de-kapperij": {
        "name": "De Kapperij",
        "address": "Oudegracht 55, 3511 AD Utrecht",
        "phone": "+31301234567",
        "ai_name": "Laura",
        "owner": "Thomas de Groot",
        "services": [
            {"name": "knippen", "price": 22, "duration_min": 30},
            {"name": "verven", "price": 55, "duration_min": 60},
            {"name": "föhnen", "price": 18, "duration_min": 15},
            {"name": "kinderknippen", "price": 15, "duration_min": 20},
        ],
        "stylists": ["Thomas", "Emma", "Noah"],
        "opening_hours": {
            "monday":    {"open": "09:00", "close": "17:00"},
            "tuesday":   {"open": "09:00", "close": "17:00"},
            "wednesday": {"open": "09:00", "close": "17:00"},
            "thursday":  {"open": "09:00", "close": "17:00"},
            "friday":    {"open": "09:00", "close": "17:00"},
            "saturday":  {"open": "09:00", "close": "13:00"},
            "sunday":    None,
        },
        "slot_interval_min": 30,
    },
    "haar-en-co": {
        "name": "Haar & Co",
        "address": "Passage 23, 2511 AB Den Haag",
        "phone": "+31701234567",
        "ai_name": "Sophie",
        "owner": "Fatima El Amrani",
        "services": [
            {"name": "knippen", "price": 30, "duration_min": 30},
            {"name": "verven", "price": 70, "duration_min": 60},
            {"name": "föhnen", "price": 25, "duration_min": 15},
            {"name": "bruidskapsel", "price": 95, "duration_min": 90},
        ],
        "stylists": ["Fatima", "Yara", "Noor"],
        "opening_hours": {
            "monday":    {"open": "09:00", "close": "18:00"},
            "tuesday":   {"open": "09:00", "close": "18:00"},
            "wednesday": {"open": "09:00", "close": "18:00"},
            "thursday":  {"open": "09:00", "close": "20:00"},
            "friday":    {"open": "09:00", "close": "18:00"},
            "saturday":  {"open": "09:00", "close": "17:00"},
            "sunday":    None,
        },
        "slot_interval_min": 30,
    },
    "mane-attractie": {
        "name": "Mane Attractie",
        "address": "Stratumseind 14, 5611 EN Eindhoven",
        "phone": "+31401234567",
        "ai_name": "Jesse",
        "owner": "Robin Smit",
        "services": [
            {"name": "knippen", "price": 24, "duration_min": 30},
            {"name": "verven", "price": 58, "duration_min": 60},
            {"name": "föhnen", "price": 19, "duration_min": 15},
            {"name": "baard trimmen", "price": 16, "duration_min": 20},
        ],
        "stylists": ["Robin", "Jesse", "Sam"],
        "opening_hours": {
            "monday":    {"open": "09:00", "close": "18:00"},
            "tuesday":   {"open": "09:00", "close": "18:00"},
            "wednesday": {"open": "09:00", "close": "18:00"},
            "thursday":  {"open": "09:00", "close": "18:00"},
            "friday":    {"open": "09:00", "close": "18:00"},
            "saturday":  {"open": "09:00", "close": "14:00"},
            "sunday":    None,
        },
        "slot_interval_min": 30,
    },
}

def get_business(business_id):
    """Haal een business op via ID. Return None als die niet bestaat."""
    return BUSINESSES.get(business_id)
