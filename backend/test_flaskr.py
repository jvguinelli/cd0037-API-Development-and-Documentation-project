import unittest
import json
import random

from flaskr import create_app
from models import db, Category, Question

QUESTIONS_PER_PAGE = 10


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.database_name = "trivia_test"
        self.database_path = "postgresql://{}:{}@{}/{}".format(
                "student",
                "student",
                "localhost:5432",
                self.database_name
            )

        test_config = {
            'SQLALCHEMY_DATABASE_URI': self.database_path,
            'SQLALCHEMY_TRACK_MODIFICATIONS': False
        }

        self.app = create_app(test_config)
        self.client = self.app.test_client

        # binds the app to the current context
        with self.app.app_context():
            self.db = db
            # create all tables
            self.db.create_all()

        self.new_question = {
            "question": "How many World Cups did Brazil win?",
            "answer": "5",
            "difficulty": 1,
            "category": 6
        }

    def tearDown(self):
        """Executed after reach test"""
        pass

    """
    TODO
    Write at least one test for each test for successful operation and for
        expected errors.
    """

    def assert_error404(self, res):
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['error'], 404)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], "not found")

    def test_get_categories(self):
        res = self.client().get('/categories')
        data = json.loads(res.data)

        categories_dict = {}
        with self.app.app_context():
            categories = Category.query.all()

        for category in categories:
            categories_dict[category.id] = category.type

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertListEqual(
            list(data['categories'].values()),
            list(categories_dict.values())
        )

    def test_get_paginated_questions(self):
        page = 1
        res = self.client().get(f'/questions?page={page}')
        data = json.loads(res.data)

        with self.app.app_context():
            questions = Question.query \
                            .order_by(Question.id) \
                            .paginate(page=page, per_page=QUESTIONS_PER_PAGE)

            questions_lst = [question.format() for question in questions]

            categories = Category.query.all()

            categories_dict = {}
            for category in categories:
                categories_dict[category.id] = category.type

            self.assertEqual(res.status_code, 200)
            self.assertListEqual(data['questions'], questions_lst)
            self.assertEqual(data['total_questions'], questions.total)
            self.assertListEqual(
                    list(data['categories'].values()),
                    list(categories_dict.values())
                )
            self.assertIsNone(data['current_category'])

    def test_404_sent_invalid_page(self):
        res = self.client().get('/questions?page=100')
        self.assert_error404(res)

    def test_deleting_question(self):
        with self.app.app_context():
            # get a randon question id to delete
            questions_ids = Question.query.with_entities(Question.id).all()
            randon_question = random.randint(0, len(questions_ids) - 1)
            question_id = questions_ids[randon_question].id

            res = self.client().delete(f'/questions/{question_id}')
            data = json.loads(res.data)

            self.assertEqual(res.status_code, 200)
            self.assertTrue(data['success'])
            self.assertEqual(data['deleted'], question_id)
            # assert the question was deleted from database
            question_count = Question.query\
                .filter(Question.id == data['deleted'])\
                .count()
            self.assertEqual(question_count, 0)

    def test_404_deleting_non_existent_question(self):
        res = self.client().delete('/questions/1000')
        self.assert_error404(res)

    def test_create_question(self):
        res = self.client().post('/questions', json=self.new_question)
        data = json.loads(res.data)

        with self.app.app_context():
            self.assertEqual(res.status_code, 201)
            self.assertTrue(data['success'])
            self.assertTrue(data['created'])

            # assert the new question was created in database
            question_count = Question.query\
                .filter(Question.id == data['created'])\
                .count()
            self.assertEqual(question_count, 1)

    def test_422_unprocessable_wrong_category(self):
        res = self.client().post(
            '/questions',
            json={
                "question": "How many World Cups did Brazil win?",
                "answer": "5",
                "difficulty": 1,
                "category": "SPORT"
            }
        )
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 422)
        self.assertEqual(data['message'], "unprocessable")

    def test_question_search(self):
        search_term = "artist"
        res = self.client().post(
            '/questions/search',
            json={"searchTerm": search_term}
        )
        data = json.loads(res.data)

        with self.app.app_context():
            questions = Question.query \
                            .order_by(Question.id) \
                            .filter(
                                Question.question.ilike(f"%{search_term}%")
                            )

            questions = [question.format() for question in questions]

            self.assertEqual(res.status_code, 200)
            self.assertTrue(data['success'])
            self.assertListEqual(data['questions'], questions)
            self.assertEqual(data['totalQuestions'], len(questions))
            self.assertIsNone(data['currentCategory'])

    def test_404_no_question_found(self):
        res = self.client().post(
            '/question',
            json={"searchTerm": "grth"}
        )

        self.assert_error404(res)

    def test_get_questions_by_category(self):
        category_id = 1
        res = self.client().get(f'/categories/{category_id}/questions')
        data = json.loads(res.data)

        with self.app.app_context():
            questions = Question.query \
                            .filter(Question.category == category_id)\
                            .order_by(Question.id) \
                            .all()

            questions_lst = [question.format() for question in questions]

            self.assertEqual(res.status_code, 200)
            self.assertTrue(data['success'])
            self.assertListEqual(data['questions'], questions_lst)
            self.assertEqual(data['total_questions'], len(questions_lst))
            self.assertEqual(data['current_category'], category_id)

    def test_404_no_question_found_in_category(self):
        res = self.client().get('/categories/1000/questions')

        self.assert_error404(res)

    def test_get_quiz_question(self):
        quiz_category = 1
        previous_question = [21]
        res = self.client().post(
            '/quizzes',
            json={
                "previous_questions": previous_question,
                "quiz_category": quiz_category
            }
        )
        data = json.loads(res.data)

        with self.app.app_context():
            # get the ids from all questions in a given category
            questions_ids = Question.query\
                                .filter(Question.category == quiz_category)\
                                .with_entities(Question.id)\
                                .all()
            questions_ids = [question_id[0]
                             for question_id in questions_ids]

            # remove the id that was sent as previous_question to the server
            questions_ids = list(set(questions_ids) - set(previous_question))

            self.assertEqual(res.status_code, 200)
            self.assertTrue(data['success'])
            self.assertEqual(data['question']['category'], quiz_category)

            # Assert the question is one that has not been returned yet
            self.assertIn(data['question']['id'], questions_ids)

    def test_404_no_more_questions(self):
        with self.app.app_context():
            category = 1
            # get the ids from all questions in a given category
            questions_ids = Question.query\
                                    .filter(Question.category == category)\
                                    .with_entities(Question.id)\
                                    .all()
            questions_ids = [question_id[0]
                             for question_id in questions_ids]

            # inform all questions ids as 'previous_questions' so that
            # there is no more question to be returned
            res = self.client().post(
                '/quizzes',
                json={
                    "previous_questions": questions_ids,
                    "quiz_category": category
                }
            )

            self.assert_error404(res)

    def test_404_no_questions_in_category(self):
        res = self.client().post(
            '/quizzes',
            json={
                "previous_questions": [],
                "quiz_category": 1000
            }
        )

        self.assert_error404(res)


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
