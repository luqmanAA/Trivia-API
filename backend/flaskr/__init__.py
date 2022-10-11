import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def all_categories():
    categories = Category.query.order_by(Category.id).all()
    return {category.id: category.type for category in categories}


def all_questions():
    return Question.query.order_by(Question.id).all()


def get_random_question(previous_question, questions):
    random_question = random.choice(questions)
    if random_question.id in previous_question:
        if len(questions) == len(previous_question):
            return False
        return get_random_question(previous_question, questions)
    return random_question


def paginated_questions(request, questions):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    formatted_questions = [question.format() for question in questions]

    return formatted_questions[start:end]


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)

    with app.app_context():
        setup_db(app)
    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """

    # CORS Headers
    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response

    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """

    @app.route('/categories', methods=['GET'])
    def get_categories():
        categories = all_categories()
        return jsonify({
            "success": True,
            "categories": categories,
            "total_categories": len(categories)
        })

    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """

    @app.route('/questions', methods=['GET'])
    def get_questions():
        questions = all_questions()
        current_questions = paginated_questions(request, questions)
        if not current_questions:
            abort(404)
        return jsonify({
            "success": True,
            "questions": current_questions,
            "categories": all_categories(),
            "total_questions": len(questions)
        })

    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(Question.id == question_id).one_or_none()
            if not question:
                abort(404)
            question.delete()
            questions = all_questions()
            current_questions = paginated_questions(request, questions)
            return jsonify({
                'success': True,
                'deleted': question_id,
                'questions': current_questions,
                'total_questions': len(questions)
            })
        except:
            abort(404)

    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """

    @app.route('/questions', methods=['POST'])
    def add_question():
        body = request.get_json()
        new_question = {
            'question': body.get('question'),
            'answer': body.get('answer'),
            'category': body.get('category'),
            'difficulty': body.get('difficulty')
        }
        search_term = body.get('searchTerm')
        try:
            if search_term:
                questions = Question.query.order_by(Question.id).filter(
                    Question.question.ilike('%{}%'.format(search_term))
                )
                current_questions = paginated_questions(request, questions)
                return jsonify({
                    'success': True,
                    'questions': current_questions,
                    'total_questions': len(all_questions()),
                    'categories': all_categories()
                })
            if not new_question['question'] or not new_question['answer']:
                raise ValueError("Empty question or answer field for new entry")
            question = Question(**new_question)
            question.insert()
            questions = all_questions()
            current_questions = paginated_questions(request, questions)
            if not current_questions:
                abort(404)
            return jsonify({
                "success": True,
                "created": question.id,
                "questions": current_questions,
                "categories": all_categories(),
                "total_questions": len(questions)
            })
        except:
            abort(422)

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """

    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """

    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_category_questions(category_id):
        try:
            category = Category.query.filter(Category.id == category_id).one_or_none()
            if not category:
                abort(404)
            questions = Question.query.filter(Question.category == category.id).all()
            if not questions:
                abort(404)
            current_questions = paginated_questions(request, questions)
            return jsonify({
                "success": True,
                "questions": current_questions,
                "categories": all_categories(),
                "current_category": category.format(),
                "total_questions": len(questions)
            })
        except:
            abort(404)

    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """

    @app.route('/quizzes', methods=['POST'])
    def take_quiz():
        body = request.get_json()
        previous_questions = body.get('previous_questions')
        quiz_category = body.get('quiz_category')
        if quiz_category['id'] == 0:
            questions = Question.query.all()
        else:
            questions = Question.query.filter(Question.category == quiz_category['id']).all()
        if not questions:
            abort(404)
        random_question = get_random_question(previous_questions, questions)
        if not random_question:
            return jsonify({
                'success': True,
                'question': None,
            })
        return jsonify({
            'success': True,
            'question': random_question.format(),
        })

    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "bad request"
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404

    @app.errorhandler(405)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "method not allowed"
        }), 405

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    @app.errorhandler(500)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "unprocessable"
        }), 500

    return app
