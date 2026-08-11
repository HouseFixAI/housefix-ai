"""
DC Configuration — Yard Management System.
"""

DCS = {
    "dc-rotterdam": {
        "name": "Distributiecentrum Rotterdam Smirnoffweg",
        "address": "Smirnoffweg 42, 3044 AP Rotterdam",
        "standby_slots": 2,
        "reistijd_minuten": 8,
        "timeout_standby": 15,       # minutes before no-show if standby expires
        "timeout_dock": 10,          # minutes before no-show if dock expires
        "no_show_limit": 2,          # max no-shows before block
        "block_hours": 24,           # hours blocked after limit reached
    },
}

# Dock names to seed per DC
DEFAULT_DOCKS = ["Dok A", "Dok B", "Dok C"]

# Valid state transitions (from → to)
# Reversed for quick lookup
VALID_TRANSITIONS = {
    "Ingecheckt":       ["Wachtend", "No_Show"],
    "Wachtend":         ["Truckparking", "Standby_Onderweg", "No_Show"],
    "Truckparking":     ["Standby_Onderweg", "No_Show"],
    "Standby_Onderweg": ["Standby_Aangekomen", "No_Show"],
    "Standby_Aangekomen": ["Actief_Dok", "No_Show"],
    "Actief_Dok":       ["Voltooid", "No_Show"],
    "Voltooid":         [],          # terminal state
    "No_Show":          ["Wachtend", "Geblokkeerd"],
    "Geblokkeerd":      [],          # terminal state
}

# SMS/instructions in 4 languages per status
INSTRUCTIONS = {
    "Ingecheckt": {
        "NL": "U bent ingecheckt. Wacht op verdere instructies. Uw positie in de wachtrij: {position}.",
        "EN": "You are checked in. Wait for further instructions. Your position in queue: {position}.",
        "PL": "Jesteś zameldowany. Czekaj na dalsze instrukcje. Twoja pozycja w kolejce: {position}.",
        "RO": "Sunteți înregistrat. Așteptați instrucțiuni suplimentare. Poziția dvs. în coadă: {position}.",
    },
    "Wachtend": {
        "NL": "U staat in de wachtrij. Positie: {position}. Houd uw telefoon in de gaten.",
        "EN": "You are in the queue. Position: {position}. Keep an eye on your phone.",
        "PL": "Jesteś w kolejce. Pozycja: {position}. Miej telefon przy sobie.",
        "RO": "Sunteți în coadă. Poziția: {position}. Urmăriți telefonul.",
    },
    "Truckparking": {
        "NL": "U staat op de truckparking. Positie: {position}. Wacht op oproep.",
        "EN": "You are at the truck parking. Position: {position}. Wait for call-up.",
        "PL": "Jesteś na parkingu dla ciężarówek. Pozycja: {position}. Czekaj na wezwanie.",
        "RO": "Sunteți în parcarea camioanelor. Poziția: {position}. Așteptați apelul.",
    },
    "Standby_Onderweg": {
        "NL": "Rijd naar de standby-plek. U heeft {minutes} minuten. Volg de borden 'Standby'.",
        "EN": "Drive to the standby spot. You have {minutes} minutes. Follow signs for 'Standby'.",
        "PL": "Jedź na miejsce postojowe. Masz {minutes} minut. Postępuj zgodnie ze znakami 'Standby'.",
        "RO": "Conduceți la locul de așteptare. Aveți {minutes} minute. Urmați indicatoarele 'Standby'.",
    },
    "Standby_Aangekomen": {
        "NL": "U bent aangekomen op de standby-plek. Wacht tot een dok vrijkomt.",
        "EN": "You have arrived at the standby spot. Wait for a dock to become available.",
        "PL": "Dotarłeś na miejsce postojowe. Czekaj, aż dok stanie się dostępny.",
        "RO": "Ați ajuns la locul de așteptare. Așteptați până când un doc devine disponibil.",
    },
    "Actief_Dok": {
        "NL": "U bent toegewezen aan {dock}. U heeft {minutes} minuten om te lossen.",
        "EN": "You are assigned to {dock}. You have {minutes} minutes to unload.",
        "PL": "Zostałeś przydzielony do {dock}. Masz {minutes} minut na rozładunek.",
        "RO": "Sunteți repartizat la {dock}. Aveți {minutes} minute pentru descărcare.",
    },
    "Voltooid": {
        "NL": "Afgerond. Bedankt en goede reis!",
        "EN": "Completed. Thank you and have a safe journey!",
        "PL": "Zakończone. Dziękujemy i życzymy bezpiecznej podróży!",
        "RO": "Finalizat. Vă mulțumim și călătorie sigură!",
    },
    "No_Show": {
        "NL": "U bent niet op tijd verschenen. Dit is no-show {count} van {limit}. Neem contact op met de expediteur.",
        "EN": "You did not appear on time. This is no-show {count} of {limit}. Contact your dispatcher.",
        "PL": "Nie pojawiłeś się na czas. To nieobecność {count} z {limit}. Skontaktuj się z dyspozytorem.",
        "RO": "Nu v-ați prezentat la timp. Aceasta este absența {count} din {limit}. Contactați dispecerul.",
    },
    "Geblokkeerd": {
        "NL": "Uw kenteken is geblokkeerd voor {hours} uur vanwege herhaaldelijk niet verschijnen.",
        "EN": "Your license plate is blocked for {hours} hours due to repeated no-shows.",
        "PL": "Twoja tablica rejestracyjna jest zablokowana na {hours} godzin z powodu powtarzających się nieobecności.",
        "RO": "Numărul dvs. de înmatriculare este blocat timp de {hours} ore din cauza absențelor repetate.",
    },
}
