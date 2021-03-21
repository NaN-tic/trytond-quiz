# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import quiz

def register():
    Pool.register(
        quiz.QuizCategory,
        quiz.QuizQuestion,
        quiz.QuizQuestionOption,
        quiz.Quiz,
        quiz.QuizOption,
        module='quiz', type_='model')
