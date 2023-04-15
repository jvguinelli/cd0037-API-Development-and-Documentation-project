import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Category, Question


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = "postgres://{}/{}".format('localhost:5432',
                                                       self.database_name)
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()

        self.new_question = {
            "question": "How many World Cups did Brazil win?",
            "answer": "5",
            "difficulty": 1,
            "category": "Sports"
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
        self.assertEqual(data.error, 404)
        self.assertFalse(data.success)
        self.assertEqual(data.message, "not found")

    def test_get_categories(self):
        res = self.client().get('/categories')
        data = json.loads(res.data)

        self.assert_equal(res.status_code, 200)
        self.assertEqual(data.success, True)
        self.assertTrue(len(data.categories.keys()) > 0)

    def test_get_paginated_questions(self):
        res = self.client().get('/questions?page=1')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(data.questions.keys()) > 0)
        self.assertTrue(data.total_questions > 0)
        self.assertTrue(len(data.categories.keys()) > 0)
        self.assertIsNone(data.current_category)

    def test_404_sent_invalid_page(self):
        res = self.client().get('/questions?page=100')
        self.assert_error404(res)

    def test_deleting_question(self):
        question_id = 1
        res = self.client().delete(f'/questions/{question_id}')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data.success)
        self.assertEqual(data.deleted, question_id)

    def test_404_deleting_non_existent_question(self):
        res = self.client().delete('/questions/1000')
        self.assert_error404(res)

    def test_create_question(self):
        res = self.client().post('/questions', json=self.new_question)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 201)
        self.assertTrue(data.success)
        self.assertTrue(data.created > 0)

    def test_422_if_creation_is_unprocessable(self):
        res = self.client().post(
            '/question',
            json={"question": "missing question?"}
        )
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertFalse(data.success)
        self.assertEqual(data.error, 422)
        self.assertEqual(data.message, "unprocessable")

    def test_question_search(self):
        res = self.client().post(
            '/question',
            json={"searchTerm": "artist"}
        )
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data.success)
        self.assertTrue(data.questions)
        self.assertTrue(data.totalQuestions)
        self.assertIsNone(data.currentCategory)

    def test_404_no_question_found(self):
        res = self.client().post(
            '/question',
            json={"searchTerm": "grth"}
        )

        self.assert_error404(res)

    def test_get_questions_by_category(self):
        res = self.client().get('/categories/1/questions')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data.success)
        self.assertTrue(data.questions)
        self.assertTrue(data.totalQuestions)
        self.assertEqual(data.currentCategory, 1)

    def test_404_no_question_found_in_category(self):
        res = self.client().get('/categories/1/questions')

        self.assert_error404(res)

    def test_get_quiz_question(self):
        quiz_category = 1
        res = self.client().post(
            '/quizzes',
            json={
                "previous_questions": [],
                "quiz_category": quiz_category
            }
        )
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertTrue(data.success)
        self.assertTrue(data.question)
        self.assertEqual(data.question.category, quiz_category)

    def test_404_no_more_quiz_question(self):
        res = self.client().post(
            '/quizzes',
            json={
                "previous_questions": [],
                "quiz_category": 100
            }
        )

        self.assert_error404(res)


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
