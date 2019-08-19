from trytond.model import ModelSQL, ModelView, Workflow, fields
from trytond.pyson import Eval
from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.i18n import gettext
from trytond.exceptions import UserError

__all__ = ['QuizCategory', 'QuizQuestion', 'QuizQuestionOption', 'Quiz',
    'QuizOption']


TYPES =  [
    ('options', 'Options'),
    ('text', 'Text'),
    ('integer', 'Integer'),
    ('numeric', 'Numeric'),
    ]


class QuizCategory(ModelSQL, ModelView):
    'Quiz Category'
    __name__ = 'quiz.category'
    name = fields.Char('Name', required=True)
    parent = fields.Many2One('quiz.category', 'Parent')

    def get_rec_name(self, name):
        res = ''
        if self.parent:
            res = self.parent.rec_name + ' / '
        return res + self.name


class QuizQuestion(ModelSQL, ModelView):
    'Quiz Question'
    __name__ = 'quiz.question'
    _rec_name = 'question'
    question = fields.Text('Question', required=True)
    active = fields.Boolean('Active')
    type = fields.Selection(TYPES, 'Type', required=True)
    category = fields.Many2One('quiz.category', 'Category', required=True)
    answer_options = fields.One2Many('quiz.question.option', 'question',
        'Options', states={
            'invisible': Eval('type') != 'options',
            'required': Eval('type') == 'options',
            }, depends=['type'])
    answer_text = fields.Text('Correct Answer', states={
            'invisible': Eval('type') != 'text',
            'required': Eval('type') == 'text',
            }, depends=['type'])
    answer_integer = fields.Integer('Correct Answer', states={
            'invisible': Eval('type') != 'integer',
            'required': Eval('type') == 'integer',
            }, depends=['type'])
    answer_numeric = fields.Numeric('Correct Answer', digits=(16, 4), states={
            'invisible': Eval('type') != 'numeric',
            'required': Eval('type') == 'numeric',
            }, depends=['type'])
    explanation = fields.Text('Explanation')

    @classmethod
    def __setup__(cls):
        super(QuizQuestion, cls).__setup__()
        cls._buttons.update({
                'create_quiz': {
                    'icon': 'tryton-new',
                    },
                })

    @staticmethod
    def default_active():
        return True

    @staticmethod
    def default_type():
        return 'options'

    @classmethod
    @ModelView.button
    def create_quiz(cls, questions):
        pool = Pool()
        Quiz = pool.get('quiz')
        Party = pool.get('party.party')
        quizzes = []
        for question in questions:
            quiz = Quiz()
            quiz.party = Party(Quiz.default_party())
            quiz.date = Quiz.default_date()
            quiz.question = question
            quiz.on_change_question()
            quizzes.append(quiz)
        Quiz.save(quizzes)

    @classmethod
    def write(cls, *args):
        Quiz = Pool().get('quiz')
        actions = iter(args)
        for questions, values in zip(actions, actions):
            quizzes = Quiz.search([
                    ('question', 'in', [x.id for x in questions]),
                    ], limit=1)
            if not quizzes:
                continue
            if 'type' in values:
                raise UserError(gettext('quiz.msg_update_forbidden',
                    name=quizzes[0].rec_name,
                    ))
            raise UserError(gettext('quiz.msg_update_warning',
                name=quizzes[0].rec_name,
                ))
        super(QuizQuestion, cls).write(*args)


class QuizQuestionOption(ModelSQL, ModelView):
    'Quiz Question Option'
    __name__ = 'quiz.question.option'
    _rec_name = 'text'
    question = fields.Many2One('quiz.question', 'Question', required=True,
        ondelete='CASCADE')
    active = fields.Boolean('Active')
    text = fields.Text('Text')
    correct = fields.Boolean('Correct?', help='Mark as correct if this answer '
        'is valid.')

    @staticmethod
    def default_active():
        return True

    @classmethod
    def write(cls, *args):
        QuizOption = Pool().get('quiz.option')
        actions = iter(args)
        for qoptions, values in zip(actions, actions):
            options = QuizOption.search([
                    ('option', 'in', [x.id for x in qoptions]),
                    ], limit=1)
            if options:
                raise UserError(gettext('quiz.msg_update_warning',
                    name=options[0].rec_name,
                    ))

        super(QuizQuestionOption, cls).write(*args)


class Quiz(Workflow, ModelSQL, ModelView):
    'Quiz'
    __name__ = 'quiz'
    party = fields.Many2One('party.party', 'Party', required=True,
        ondelete='RESTRICT')
    date = fields.Date('Date', required=True, states={
            'readonly': Eval('state') != 'draft',
            })
    question = fields.Many2One('quiz.question', 'Question', required=True,
        ondelete='RESTRICT', states={
            'readonly': Eval('state') != 'draft',
            })
    question_text = fields.Function(fields.Text('Question Text'),
        'get_question_text')
    type = fields.Function(fields.Selection(TYPES, 'Type', required=True),
        'get_type')
    answer_options = fields.One2Many('quiz.option', 'quiz', 'Answer',
        states={
            'invisible': Eval('type') != 'options',
            'required': (Eval('type') == 'options') & (Eval('state') !=
                'draft'),
            'readonly': Eval('state') != 'draft',
            }, depends=['type', 'state'])
    answer_text = fields.Text('Answer', states={
            'invisible': Eval('type') != 'text',
            'required': (Eval('type') == 'text') & (Eval('state') != 'draft'),
            'readonly': Eval('state') != 'draft',
            }, depends=['type', 'state'])
    answer_integer = fields.Integer('Answer', states={
            'invisible': Eval('type') != 'integer',
            'required': (Eval('type') == 'integer') & (Eval('state') !=
                'draft'),
            'readonly': Eval('state') != 'draft',
            }, depends=['type', 'state'])
    answer_numeric = fields.Numeric('Answer', digits=(16, 4), states={
            'invisible': Eval('type') != 'numeric',
            'required': (Eval('type') == 'numeric') & (Eval('state') !=
                'draft'),
            'readonly': Eval('state') != 'draft',
            }, depends=['type', 'state'])
    state = fields.Selection([
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('evaluated', 'Evaluated'),
            ], 'State', required=True, readonly=True)
    correct = fields.Boolean('Correct?', readonly=True)

    @classmethod
    def __setup__(cls):
        super(Quiz, cls).__setup__()
        cls._buttons.update({
                'submit': {
                    'invisible': Eval('state') != 'draft',
                    'icon': 'tryton-forward',
                    },
                'draft': {
                    'invisible': Eval('state') != 'submitted',
                    'icon': 'tryton-back',
                    },
                'evaluate': {
                    'invisible': Eval('state') != 'submitted',
                    'icon': 'tryton-ok',
                    }
                })
        cls._transitions |= set((
            ('draft', 'submitted'),
            ('submitted', 'draft'),
            ('submitted', 'evaluated'),
            ))

    @staticmethod
    def default_party():
        pool = Pool()
        User = pool.get('res.user')
        Employee = pool.get('company.employee')
        employee_id = None
        if Transaction().context.get('employee'):
            employee_id = Transaction().context['employee']
        else:
            user = User(Transaction().user)
            if user.employee:
                employee_id = user.employee.id
        if employee_id:
            return Employee(employee_id).party.id

    @staticmethod
    def default_date():
        Date = Pool().get('ir.date')
        return Date.today()

    @staticmethod
    def default_state():
        return 'draft'

    @fields.depends('question')
    def on_change_question(self):
        QuizOption = Pool().get('quiz.option')
        if not self.question:
            return
        self.question_text = self.question.question
        self.type = self.question.type
        options = []
        for option in self.question.answer_options:
            options.append(QuizOption(option=option, text=option.text))
        self.answer_options = options

    def get_question_text(self, name=None):
        if self.question:
            return self.question.question

    def get_type(self, name):
        return self.question.type

    @classmethod
    @Workflow.transition('submitted')
    @ModelView.button
    def submit(cls, quizzes):
        pass

    @classmethod
    @Workflow.transition('draft')
    @ModelView.button
    def draft(cls, quizzes):
        pass

    @classmethod
    @Workflow.transition('evaluated')
    @ModelView.button
    def evaluate(cls, quizzes):
        for quiz in quizzes:
            quiz.evaluate_one()
        cls.save(quizzes)

    def evaluate_one(self):
        if self.type == 'options':
            self.correct = True
            assert len(self.answer_options) == len(self.question.answer_options)
            for option in self.answer_options:
                if option.checked == option.option.correct:
                    option.correct = True
                else:
                    option.correct = False
                    self.correct = False
                # Would be great to avoid this but it seems that the save on
                # evaluate does not save the changes in the options.
                option.save()
        elif self.type == 'text':
            valid = self.question.answer_text.strip().lower()
            self.correct = self.answer_text.lower() == valid
        elif self.type == 'integer':
            self.correct = self.answer_integer == self.question.answer_integer
        elif self.type == 'numeric':
            self.correct = self.answer_numeric == self.question.answer_numeric

    @classmethod
    def copy(cls, quizzes, default=None):
        Date = Pool().get('ir.date')
        if default is None:
            default = {}
        for field in ('answer_text', 'answer_integer', 'answer_numeric'):
            if not field in default:
                default[field] = None
        if not 'state' in default:
            default['state'] = 'draft'
        if not 'correct' in default:
            default['correct'] = False
        if not 'date' in default:
            default['date'] = Date.today()
        return super(Quiz, cls).copy(quizzes, default)


class QuizOption(ModelSQL, ModelView):
    'Quiz Option'
    __name__ = 'quiz.option'
    quiz = fields.Many2One('quiz', 'Quiz', required=True, ondelete='CASCADE')
    option = fields.Many2One('quiz.question.option', 'Option', required=True,
        ondelete='RESTRICT')
    text = fields.Function(fields.Text('Text'), 'get_text')
    checked = fields.Boolean('Check?')
    correct = fields.Boolean('Correct?', readonly=True)

    def get_text(self, name):
        return self.option.text

    @classmethod
    def copy(cls, options, default=None):
        if default is None:
            default = {}
        if not 'checked' in default:
            default['checked'] = False
        if not 'correct' in default:
            default['correct'] = False
        return super(QuizOption, cls).copy(options, default)
