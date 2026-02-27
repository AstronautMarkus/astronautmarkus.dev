from flask import render_template
from . import home_bp
from datetime import datetime
import random
from app.models.models import Visit


def _format_visitor_counter(total_visits: int) -> str:
    if total_visits <= 9999:
        return f"{total_visits:04d}"
    return str(total_visits)

@home_bp.route('/')
def index():

    visitor_counter = Visit.query.count()
    visitor_counter_formatted = _format_visitor_counter(visitor_counter)

    born_day = 'March 16, 2003'

    current_year = datetime.now().year
    born_year = datetime.strptime('2003-03-16', '%Y-%m-%d').year

    current_age = current_year - born_year

    quotes = [
        "IF THE CODE WORKS, DON'T TOUCH IT!! - 2003, CREATED BY A HUMAN, FOR HUMANS",
        "HOLD ON, IF LOVE IS THE ANSWER, YOU'RE HOME.",
        "I'M NOT A ROBOT, I'M A HUMAN BEING.",
        "IN A WORLD OF BAD PEOPLE, THE GREATEST ACT OF REBELLION IS TO BE GOOD.",
        "TECHNOLOGY IS REPLACEABLE, PEOPLE ARE NOT.",
        "BE HAPPY OR FIT INTO SOCIETY?",
        "THE DESTINY OF GREAT SOULS IS TO BE CRITICIZED BY THE MEDIOCRE ONES.",
        "NO MATTER WHERE YOU GO, EVERYBODY'S CONNECTED.",
        "NOW IS YOUR CHANCE TO BE A BIG SHOT!"
    ]

    random_quote = random.choice(quotes)

    return render_template(
        'index.html',
        age=current_age,
        born_day=born_day,
        quote=random_quote,
        visitor_counter=visitor_counter_formatted
    )

@home_bp.route('/es')
def index_es():

    visitor_counter = Visit.query.count()
    visitor_counter_formatted = _format_visitor_counter(visitor_counter)

    born_day = '16 de marzo de 2003'

    current_year = datetime.now().year
    born_year = datetime.strptime('2003-03-16', '%Y-%m-%d').year

    current_age = current_year - born_year

    quotes = [
        "SI EL CÓDIGO FUNCIONA, ¡NO LO TOQUES! - 2003, CREADO POR UN HUMANO, PARA HUMANOS",
        "NO SOY UN ROBOT, SOY UN SER HUMANO.",
        "EN UN MUNDO DE MALAS PERSONAS, EL MAYOR ACTO DE REBELIÓN ES SER BUENO.",
        "LA TECNOLOGÍA ES REEMPLAZABLE, LAS PERSONAS NO.",
        "¿SER FELIZ O ENCAJAR EN LA SOCIEDAD?",
        "EL DESTINO DE LAS GRANDES ALMAS ES SER CRITICADAS POR LOS MEDIOCRES.",
        "NO IMPORTA A DÓNDE VAYAS, TODOS ESTÁN CONECTADOS."
    ]

    random_quote = random.choice(quotes)

    return render_template(
        '/es/index.html',
        age=current_age,
        born_day=born_day,
        quote=random_quote,
        visitor_counter=visitor_counter_formatted
    )