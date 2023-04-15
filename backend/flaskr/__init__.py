from flask import Flask, request, abort, jsonify
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)

    if test_config:
        app.config.from_mapping(test_config)
    else:
        app.config.from_object('config')

    setup_db(app)

    """
    @TODO: Set up CORS. Allow '*' for origins.
            Delete the sample route after completing the TODOs
    """
    CORS(app, resources={r"*": {"origins": "*"}})

    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PATCH,POST,DELETE,OPTIONS')
        return response

    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """
    @app.route('/categories', methods=['GET'])
    def categories():
        categories = Category.query.all()

        categories_dict = {}
        for category in categories:
            categories_dict[category.id] = category.type

        return jsonify({
            "success": True,
            "categories": categories_dict
        })

    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen
        for three pages.
    Clicking on the page numbers should update the questions.
    """
    @app.route('/questions', methods=['GET'])
    def questions():
        page = request.args.get('page', None, int)
        questions = Question.query \
                            .order_by(Question.id) \
                            .paginate(page=page, per_page=QUESTIONS_PER_PAGE)

        questions_lst = [question.format() for question in questions]

        if len(questions_lst) == 0:
            abort(404)

        categories = Category.query.all()

        categories_dict = {}
        for category in categories:
            categories_dict[category.id] = category.type

        return jsonify({
            "questions": questions_lst,
            "total_questions": questions.total,
            "categories": categories_dict,
            "current_category": None
        })

    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question,
            the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def del_question(question_id):
        question = Question.query.get_or_404(question_id)
        question.delete()
        return jsonify({
            "success": True,
            "deleted": question_id
        })

    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear
        at the end of the last page
    of the questions list in the "List" tab.
    """

    @app.route('/questions', methods=['POST'])
    def create_question():
        try:
            json_data = request.get_json()
            question = json_data.get('question', None)
            answer = json_data.get('answer', None)
            difficulty = json_data.get('difficulty', None)
            category = json_data.get('category', None)

            question = Question(question, answer, difficulty, category)
            question.insert()

            return jsonify({
                "success": True,
                "created": question.id
            }), 201

        except Exception:
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

    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        json_data = request.get_json()
        search_term = json_data.get('searchTerm', '')

        questions = Question.query \
                            .order_by(Question.id) \
                            .filter(
                                Question.question.ilike(f"%{search_term}%")
                            )

        questions = [question.format() for question in questions]

        if len(questions) == 0:
            abort(404)

        return jsonify({
            "success": True,
            "questions": questions,
            "totalQuestions": len(questions),
            "currentCategory": None,
          })

    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """

    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def questions_by_category(category_id):
        questions = Question.query \
                            .filter(Question.category == category_id)\
                            .order_by(Question.id) \
                            .all()

        questions_lst = [question.format() for question in questions]

        if len(questions_lst) == 0:
            abort(404)

        return jsonify({
            "success": True,
            "questions": questions_lst,
            "total_questions": len(questions_lst),
            "current_category": category_id
        })

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
    def next_question():
        json_data = request.get_json()
        previous_questions = json_data.get('previous_questions', '')
        category = json_data.get('quiz_category', '')

        query = Question.query \
                        .filter(Question.id.not_in(previous_questions)) \

        if category and (category != 0):
            query = query.filter(Question.category == category)

        qtd_questions = query.count()
        pos_question = None
        if qtd_questions == 0:
            abort(404)
        elif qtd_questions == 1:
            pos_question = 1
        else:
            pos_question = random.randint(0, qtd_questions - 1)

        question = query.order_by(Question.id) \
                        .offset(pos_question).first()


        question = question.format()

        return jsonify({
            "success": True,
            "question": question
        })

    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """

    @app.errorhandler(400)
    def bad_request(error):
        return (
            jsonify({
                "success": False,
                "error": 400,
                "message": "bad request"
            }), 400,
        )

    @app.errorhandler(404)
    def not_fount(error):
        return (
            jsonify({
                "success": False,
                "error": 404,
                "message": "not found"
            }), 404,
        )

    @app.errorhandler(405)
    def not_allowed(error):
        return (
            jsonify({
                "success": False,
                "error": 405,
                "message": "method not allowed"
            }),
            405,
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({
                "success": False,
                "error": 422,
                "message": "unprocessable"
            }), 422,
        )

    return app
