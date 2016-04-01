# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .quiz import *

def register():
    Pool.register(
        QuizCategory,
        QuizQuestion,
        QuizQuestionOption,
        Quiz,
        QuizOption,
        module='quiz', type_='model')
