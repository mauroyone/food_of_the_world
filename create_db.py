from app import app, db
from app.models import AvailableCountries
from flask_login import current_user

def create_country_table():
    i = 0
    with open('country_list.csv', 'r') as file:
        for line in file:
            if i > 9:
                break
            line = line.split(',')
            country = AvailableCountries(country=line[0], capital=line[1],
                                        flag_url='http://{}.com'.format(line[0]), available=current_user)
            db.session.add(country)
            db.session.commit()
            i += 1

        