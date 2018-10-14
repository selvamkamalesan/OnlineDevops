from django.contrib.auth.decorators import login_required
from django.http import request, HttpRequest, Http404, HttpResponseServerError, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from decimal import Decimal
import random

from .models import Question, Grade, Quiz, CourseModule

site_hdr = "The DevOps Course"

NUM_RAND_QS = 10

def get_filenm(mod_nm):
    return mod_nm + '.html'


def get_quiz(request, mod_nm):

    #  Returns list of Randomized Questions
    # :param: mod_nm
    # :return: header, list() containing randomized questions, mod_nm
    try:
        questions = Question.objects.filter(module=mod_nm)
        num_questions = questions.count()
        rand_qs = []
        num_qs_to_randomize = NUM_RAND_QS

        if num_questions > 0:
            # we have to fetch numq from here:
            quizzes = Quiz.objects.filter(module=mod_nm)

            if num_questions >= num_qs_to_randomize:
                    rand_qs = random.sample(list(questions),
                                            num_qs_to_randomize)
            else:
                    rand_qs = random.sample(list(questions),
                                            num_questions)

        return render(request, get_filenm(mod_nm),
                      {'header': site_hdr, 'questions': rand_qs,
                       'mod_nm': mod_nm})

        # And if we crashed along the way - we crash gracefully...
    except Exception as e:
        return HttpResponseServerError(e.__cause__,
                                       e.__context__,
                                       e.__traceback__)

def index(request: request) -> object:
    return render(request, 'index.html', {'header': site_hdr})


def about(request: request) -> object:
    return render(request, 'about.html', {'header': site_hdr})


def gloss(request: request) -> object:
    return render(request, 'gloss.html', {'header': site_hdr})


def teams(request: request) -> object:
    return render(request, 'teams.html', {'header': site_hdr})

def basics(request: request) -> object:
    return get_quiz(request, 'basics')

def build(request: request) -> object:
    return get_quiz(request, 'build')


def cloud(request: request) -> object:
    return get_quiz(request, 'cloud')


def comm(request: request) -> object:
    return get_quiz(request, 'comm')


def flow(request: request) -> object:
    return get_quiz(request, 'flow')


def incr(request: request) -> object:
    return get_quiz(request, 'incr')


def infra(request: request) -> object:
    return get_quiz(request, 'infra')


def micro(request: request) -> object:
    return get_quiz(request, 'micro')


def monit(request: request) -> object:
    return get_quiz(request, 'monit')


def no_quiz(request: request) -> object:
    return get_quiz(request, 'no_quiz')


def secur(request: request) -> object:
    return get_quiz(request, 'secur')


def sum(request: request) -> object:
    return get_quiz(request, 'sum')


def test(request: request) -> object:
    return get_quiz(request, 'test')


def work(request: request) -> object:
    return get_quiz(request, 'work')

def grade_quiz(request: HttpRequest()) -> list:
    """
    Returns list of Questions user answered as right / wrong
    :param request: request as HttpRequest()
    :return: list() of dict() containing question, right/wrong, correct answer
    """
    try:
        # First, we process only when form is POSTed...
        if request.method == 'POST':
            graded_answers = []
            user_answers = []
            form_data = request.POST
            num_correct = 0

            # get only post fields containing user answers...
            for key, value in form_data.items():
                if key.startswith('_'):
                    proper_id = str(key).strip('_')
                    user_answers.append({proper_id: value})

            # forces user to answer all quiz questions,
            # redirects to module page if not completed
            # TODO: keep previously selected radio buttons 
            # checked instead of clearing form
            mod_nm = form_data['submit']

            questions = Question.objects.filter(module=mod_nm)
            questions_count = questions.count()

            # can't do this this way: no 404s
            # please write a query that checks for result,
            # and have a default if no result
            # num_rand_qs = get_object_or_404(Quiz, module=mod_nm).numq
            num_rand_qs = 10  # temporary!

            if questions_count >= num_rand_qs:
                num_ques_of_quiz = num_rand_qs
            else:
                num_ques_of_quiz = questions_count

            number_of_ques_to_check = num_ques_of_quiz
            # Number of randomized questions from get_quiz.

            if len(user_answers) != number_of_ques_to_check:
                messages.warning(request,
                                 'Please complete all questions before submitting')
                return redirect('/devops/' + mod_nm)

            # now get those answers from database & check if answer is right...
            for answered_question in user_answers:
                processed_answer = {}
                id_to_retrieve = next(iter(answered_question))
                original_question = get_object_or_404(Question, pk=id_to_retrieve)

                # Lets start building a dict with the status for this particular question...
                # Following the DRY principle - here comes shared part for both cases...
                processed_answer['question'] = original_question.text
                processed_answer['correctAnswer'] = original_question.correct.lower()
                processed_answer['yourAnswer'] = answered_question[id_to_retrieve]

                correctanskey = "answer{}".format(processed_answer['correctAnswer'].upper())
                youranskey = "answer{}".format(processed_answer['yourAnswer'].upper())

                processed_answer['correctAnswerText'] = getattr(original_question, correctanskey)
                processed_answer['yourAnswerText'] = getattr(original_question, youranskey)

                # and now we are evaluating either as right or wrong...
                if answered_question[id_to_retrieve] == processed_answer['correctAnswer']:
                    processed_answer['message'] = "Congrats, thats correct!"
                    processed_answer['status'] = "right"
                    num_correct += 1
                else:
                    processed_answer['message'] = "Sorry, that's incorrect!"
                    processed_answer['status'] = "wrong"
                    # and store to ship to the Template.
                graded_answers.append(processed_answer)

            # Calculating quiz score
            correct_pct = Decimal((num_correct
                                                   / number_of_ques_to_check)
                                                  * 100)
            curr_quiz = Quiz.objects.get(module=mod_nm)

            # this code just assumes that the query below works!
            # can't code like that!
            # curr_module = CourseModule.objects.get(module=mod_nm)

            navigate_links = {}

            # No matter if user passes or fails, 
            # show link to next module if it exists
#            navigate_links = {
#                'next': 'devops:'
#                + curr_module.next_module if curr_module.next_module else False
#            }
#
#            # If user fails, show link to previous module
#            if (correct_pct < curr_quiz.minpass):
#                navigate_links['previous'] = 'devops:' + mod_nm

            # now we are ready to record quiz results...
            if request.user.username != '':
                action_status = Grade.objects.create(participant=request.user,
                                                     score=correct_pct.real,
                                                     quiz=curr_quiz,
                                                     quiz_name=mod_nm)

            # ok, all questions processed, lets render results...
            return render(request,
                          'graded_quiz.html',
                          dict(graded_answers=graded_answers,
                               num_ques=number_of_ques_to_check,
                               num_correct=num_correct,
                               correct_pct=int(correct_pct),
                               quiz_name='Quiz',  # curr_module.title,
                               navigate_links=navigate_links,
                               header=site_hdr))

        # If it is PUT, DELETE etc. we say we dont do that...
        else:
            raise HttpResponseBadRequest("ERROR: Method not allowed")

    # And if we crashed along the way - we crash gracefully...
    except Exception as e:
        return HttpResponseServerError(e.__cause__,
                                       e.__context__,
                                       e.__traceback__)
