from app import app, db
from app.models import Countries
from flask_login import current_user
from random import randint

def create_country_table():
    delete_country_table()

    with open('country_list.csv', encoding='utf8') as file:
        for line in file:
            line = line.rstrip()
            line = line.split(',')
            subline = line[0].split(' ')
            for i in range(len(subline)):
                subline[i] = subline[i].capitalize()

            url = ('https://www.countries-ofthe-world.com/flags-normal/flag-of-' +
                   '-'.join(subline) + '.png')
            country = Countries(country=line[0], capital=line[1],
                                flag_url=url, countries=current_user)
            db.session.add(country)
            db.session.commit()

def get_available_country():
    country = Countries.query.filter_by(used=False, user_id=current_user.id).all()
    if country is None:
        return
    index = randint(0, len(country)-1)
    country[index].set_used(True)
    db.session.commit()
    return country[index]

def get_used_countries():
    countries_used = Countries.query.filter_by(used=True, user_id=current_user.id).all()
    if countries_used is None:
        return
    return countries_used

def delete_country_table():
    countries = Countries.query.filter_by(user_id=current_user.id).all()

    for country in countries:
        db.session.delete(country)
    db.session.commit()