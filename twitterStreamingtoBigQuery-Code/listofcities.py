import random


citiesuk = ['London','Birmingham','Manchester','Liverpool',
'Newcastle','Nottingham',
'Sheffield',
'Leeds','Bristol','Middlesbrough (Teesside)','Leicester','Portsmouth',
'Bradford',
'Bournemouth','Reading','Huddersfield','Stoke',
            'Coventry','Birkenhead','Southampton','Hull','Sunderland','Wigan','Brighton','Southend','Edinburgh',
'Cardiff', 'London',
'Bristol',
'Kirklees',
'Fife',
'Aberdeen',
'Southampton',
'Portsmouth',
'Warrington',
'North Somerset',
'Bury',
'Luton',
'St Helens',
'Stockton-on-Tees',
'Renfrewshire',
'York',
'Thamesdown',
'Southend-on-Sea', 'London', 'London', 'London', 'London', 'London', 'Manchester','Manchester','Manchester','Birmingham','Birmingham']



def r_city():
    city = random.choice(citiesuk)
    return city


list_devs = ['Twitter for Android','Twitter Web Client','Twitter for iPhone','Twitter for iPad','Twitter Lite']


def r_source():
    source = random.choice(list_devs)
    return source