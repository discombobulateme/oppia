# coding: utf-8
#
# Copyright 2018 The Oppia Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for the suggestion gae_models."""
from __future__ import absolute_import  # pylint: disable=import-only-modules
from __future__ import unicode_literals  # pylint: disable=import-only-modules

from core.platform import models
from core.tests import test_utils

(base_models, suggestion_models) = models.Registry.import_models(
    [models.NAMES.base_model, models.NAMES.suggestion])


class SuggestionModelUnitTests(test_utils.GenericTestBase):
    """Tests for the suggestionModel class."""

    score_category = (
        suggestion_models.SCORE_TYPE_TRANSLATION +
        suggestion_models.SCORE_CATEGORY_DELIMITER + 'English')

    target_id = 'exp1'
    target_version_at_submission = 1
    change_cmd = {}

    def setUp(self):
        super(SuggestionModelUnitTests, self).setUp()
        suggestion_models.GeneralSuggestionModel.create(
            suggestion_models.SUGGESTION_TYPE_EDIT_STATE_CONTENT,
            suggestion_models.TARGET_TYPE_EXPLORATION,
            self.target_id, self.target_version_at_submission,
            suggestion_models.STATUS_IN_REVIEW, 'author_1',
            'reviewer_1', self.change_cmd, self.score_category,
            'exploration.exp1.thread_1')
        suggestion_models.GeneralSuggestionModel.create(
            suggestion_models.SUGGESTION_TYPE_EDIT_STATE_CONTENT,
            suggestion_models.TARGET_TYPE_EXPLORATION,
            self.target_id, self.target_version_at_submission,
            suggestion_models.STATUS_ACCEPTED, 'author_2',
            'reviewer_2', self.change_cmd, self.score_category,
            'exploration.exp1.thread_2')
        suggestion_models.GeneralSuggestionModel.create(
            suggestion_models.SUGGESTION_TYPE_EDIT_STATE_CONTENT,
            suggestion_models.TARGET_TYPE_EXPLORATION,
            self.target_id, self.target_version_at_submission,
            suggestion_models.STATUS_ACCEPTED, 'author_2',
            'reviewer_2', self.change_cmd, self.score_category,
            'exploration.exp1.thread_3')
        suggestion_models.GeneralSuggestionModel.create(
            suggestion_models.SUGGESTION_TYPE_EDIT_STATE_CONTENT,
            suggestion_models.TARGET_TYPE_EXPLORATION,
            self.target_id, self.target_version_at_submission,
            suggestion_models.STATUS_REJECTED, 'author_2',
            'reviewer_3', self.change_cmd, self.score_category,
            'exploration.exp1.thread_4')
        suggestion_models.GeneralSuggestionModel.create(
            suggestion_models.SUGGESTION_TYPE_EDIT_STATE_CONTENT,
            suggestion_models.TARGET_TYPE_EXPLORATION,
            self.target_id, self.target_version_at_submission,
            suggestion_models.STATUS_REJECTED, 'author_3',
            'reviewer_2', self.change_cmd, self.score_category,
            'exploration.exp1.thread_5')

    def test_get_deletion_policy(self):
        self.assertEqual(
            suggestion_models.GeneralSuggestionModel.get_deletion_policy(),
            base_models.DELETION_POLICY.LOCALLY_PSEUDONYMIZE)

    def test_has_reference_to_user_id(self):
        self.assertTrue(
            suggestion_models.GeneralSuggestionModel
            .has_reference_to_user_id('author_1')
        )
        self.assertTrue(
            suggestion_models.GeneralSuggestionModel
            .has_reference_to_user_id('author_2')
        )
        self.assertTrue(
            suggestion_models.GeneralSuggestionModel
            .has_reference_to_user_id('author_3')
        )
        self.assertTrue(
            suggestion_models.GeneralSuggestionModel
            .has_reference_to_user_id('reviewer_1')
        )
        self.assertTrue(
            suggestion_models.GeneralSuggestionModel
            .has_reference_to_user_id('reviewer_2')
        )
        self.assertTrue(
            suggestion_models.GeneralSuggestionModel
            .has_reference_to_user_id('reviewer_3')
        )
        self.assertFalse(
            suggestion_models.GeneralSuggestionModel
            .has_reference_to_user_id('id_x')
        )

    def test_score_type_contains_delimiter(self):
        for score_type in suggestion_models.SCORE_TYPE_CHOICES:
            self.assertTrue(
                suggestion_models.SCORE_CATEGORY_DELIMITER not in score_type)

    def test_create_new_object_succesfully(self):
        suggestion_models.GeneralSuggestionModel.create(
            suggestion_models.SUGGESTION_TYPE_EDIT_STATE_CONTENT,
            suggestion_models.TARGET_TYPE_EXPLORATION,
            self.target_id, self.target_version_at_submission,
            suggestion_models.STATUS_IN_REVIEW, 'author_3',
            'reviewer_3', self.change_cmd, self.score_category,
            'exploration.exp1.thread_6')

        suggestion_id = 'exploration.exp1.thread_6'

        observed_suggestion_model = (
            suggestion_models.GeneralSuggestionModel.get_by_id(suggestion_id))

        self.assertEqual(
            observed_suggestion_model.suggestion_type,
            suggestion_models.SUGGESTION_TYPE_EDIT_STATE_CONTENT)
        self.assertEqual(
            observed_suggestion_model.target_type,
            suggestion_models.TARGET_TYPE_EXPLORATION)
        self.assertEqual(
            observed_suggestion_model.target_id, self.target_id)
        self.assertEqual(
            observed_suggestion_model.target_version_at_submission,
            self.target_version_at_submission)
        self.assertEqual(
            observed_suggestion_model.status,
            suggestion_models.STATUS_IN_REVIEW)
        self.assertEqual(observed_suggestion_model.author_id, 'author_3')
        self.assertEqual(
            observed_suggestion_model.final_reviewer_id, 'reviewer_3')
        self.assertEqual(
            observed_suggestion_model.score_category, self.score_category)
        self.assertEqual(observed_suggestion_model.change_cmd, self.change_cmd)

    def test_create_suggestion_fails_if_id_collides_with_existing_one(self):
        with self.assertRaisesRegexp(
            Exception, 'There is already a suggestion with the given id: '
                       'exploration.exp1.thread_1'):
            suggestion_models.GeneralSuggestionModel.create(
                suggestion_models.SUGGESTION_TYPE_EDIT_STATE_CONTENT,
                suggestion_models.TARGET_TYPE_EXPLORATION,
                self.target_id, self.target_version_at_submission,
                suggestion_models.STATUS_IN_REVIEW, 'author_3',
                'reviewer_3', self.change_cmd,
                self.score_category, 'exploration.exp1.thread_1')

    def test_get_suggestions_by_type(self):
        queries = [(
            'suggestion_type',
            suggestion_models.SUGGESTION_TYPE_EDIT_STATE_CONTENT)]
        self.assertEqual(
            len(suggestion_models.GeneralSuggestionModel.query_suggestions(
                queries)), 5)
        queries = [('suggestion_type', 'invalid_suggestion_type')]

        with self.assertRaisesRegexp(
            Exception, 'Value u\'invalid_suggestion_type\' for property'
                       ' suggestion_type is not an allowed choice'):
            suggestion_models.GeneralSuggestionModel.query_suggestions(queries)

    def test_get_suggestion_by_author(self):
        queries = [('author_id', 'author_1')]
        self.assertEqual(
            len(suggestion_models.GeneralSuggestionModel.query_suggestions(
                queries)), 1)
        queries = [('author_id', 'author_2')]
        self.assertEqual(
            len(suggestion_models.GeneralSuggestionModel.query_suggestions(
                queries)), 3)
        queries = [('author_id', 'author_3')]
        self.assertEqual(
            len(suggestion_models.GeneralSuggestionModel.query_suggestions(
                queries)), 1)
        queries = [('author_id', 'author_invalid')]
        self.assertEqual(
            len(suggestion_models.GeneralSuggestionModel.query_suggestions(
                queries)), 0)

    def test_get_suggestion_by_reviewer(self):
        queries = [('final_reviewer_id', 'reviewer_1')]
        self.assertEqual(
            len(suggestion_models.GeneralSuggestionModel.query_suggestions(
                queries)), 1)
        queries = [('final_reviewer_id', 'reviewer_2')]
        self.assertEqual(
            len(suggestion_models.GeneralSuggestionModel.query_suggestions(
                queries)), 3)
        queries = [('final_reviewer_id', 'reviewer_3')]
        self.assertEqual(
            len(suggestion_models.GeneralSuggestionModel.query_suggestions(
                queries)), 1)
        queries = [('final_reviewer_id', 'reviewer_invalid')]
        self.assertEqual(
            len(suggestion_models.GeneralSuggestionModel.query_suggestions(
                queries)), 0)

    def test_get_suggestions_by_status(self):
        queries = [('status', suggestion_models.STATUS_IN_REVIEW)]
        self.assertEqual(
            len(suggestion_models.GeneralSuggestionModel.query_suggestions(
                queries)), 1)
        queries = [('status', suggestion_models.STATUS_REJECTED)]
        self.assertEqual(
            len(suggestion_models.GeneralSuggestionModel.query_suggestions(
                queries)), 2)
        queries = [('status', suggestion_models.STATUS_ACCEPTED)]
        self.assertEqual(
            len(suggestion_models.GeneralSuggestionModel.query_suggestions(
                queries)), 2)

    def test_get_suggestions_by_target_id(self):
        queries = [
            ('target_type', suggestion_models.TARGET_TYPE_EXPLORATION),
            ('target_id', self.target_id)
        ]
        self.assertEqual(
            len(suggestion_models.GeneralSuggestionModel.query_suggestions(
                queries)), 5)
        queries = [
            ('target_type', suggestion_models.TARGET_TYPE_EXPLORATION),
            ('target_id', 'exp_invalid')
        ]
        self.assertEqual(
            len(suggestion_models.GeneralSuggestionModel.query_suggestions(
                queries)), 0)

    def test_query_suggestions(self):
        queries = [
            ('target_type', suggestion_models.TARGET_TYPE_EXPLORATION),
            ('target_id', self.target_id)
        ]
        self.assertEqual(
            len(suggestion_models.GeneralSuggestionModel.query_suggestions(
                queries)), 5)

        queries = [
            ('target_type', suggestion_models.TARGET_TYPE_EXPLORATION),
            ('target_id', self.target_id),
            ('author_id', 'author_2')
        ]
        self.assertEqual(
            len(suggestion_models.GeneralSuggestionModel.query_suggestions(
                queries)), 3)

        queries = [
            ('target_type', suggestion_models.TARGET_TYPE_EXPLORATION),
            ('target_id', self.target_id),
            ('author_id', 'author_2'),
            ('status', suggestion_models.STATUS_ACCEPTED)
        ]
        self.assertEqual(
            len(suggestion_models.GeneralSuggestionModel.query_suggestions(
                queries)), 2)

        queries = [
            ('target_type', suggestion_models.TARGET_TYPE_EXPLORATION),
            ('target_id', self.target_id),
            ('invalid_field', 'value')
        ]
        with self.assertRaisesRegexp(
            Exception, 'Not allowed to query on field invalid_field'):
            suggestion_models.GeneralSuggestionModel.query_suggestions(queries)

        queries = [
            (
                'suggestion_type',
                suggestion_models.SUGGESTION_TYPE_EDIT_STATE_CONTENT),
            ('target_type', suggestion_models.TARGET_TYPE_EXPLORATION),
            ('target_id', self.target_id),
            ('status', suggestion_models.STATUS_IN_REVIEW),
            ('author_id', 'author_1'),
            ('final_reviewer_id', 'reviewer_1'),
            ('score_category', self.score_category)
        ]
        self.assertEqual(
            len(suggestion_models.GeneralSuggestionModel.query_suggestions(
                queries)), 1)

    def test_get_all_stale_suggestions(self):
        with self.swap(
            suggestion_models, 'THRESHOLD_TIME_BEFORE_ACCEPT_IN_MSECS', 0):
            self.assertEqual(len(
                suggestion_models.GeneralSuggestionModel
                .get_all_stale_suggestions()), 1)

        with self.swap(
            suggestion_models, 'THRESHOLD_TIME_BEFORE_ACCEPT_IN_MSECS',
            7 * 24 * 60 * 60 * 1000):
            self.assertEqual(len(
                suggestion_models.GeneralSuggestionModel
                .get_all_stale_suggestions()), 0)

    def test_get_in_review_suggestions_in_score_categories(self):
        suggestion_models.GeneralSuggestionModel.create(
            suggestion_models.SUGGESTION_TYPE_EDIT_STATE_CONTENT,
            suggestion_models.TARGET_TYPE_EXPLORATION,
            self.target_id, self.target_version_at_submission,
            suggestion_models.STATUS_IN_REVIEW, 'author_3',
            'reviewer_2', self.change_cmd, 'category1',
            'exploration.exp1.thread_6')
        suggestion_models.GeneralSuggestionModel.create(
            suggestion_models.SUGGESTION_TYPE_EDIT_STATE_CONTENT,
            suggestion_models.TARGET_TYPE_EXPLORATION,
            self.target_id, self.target_version_at_submission,
            suggestion_models.STATUS_IN_REVIEW, 'author_2',
            'reviewer_2', self.change_cmd, 'category2',
            'exploration.exp1.thread_7')
        suggestion_models.GeneralSuggestionModel.create(
            suggestion_models.SUGGESTION_TYPE_EDIT_STATE_CONTENT,
            suggestion_models.TARGET_TYPE_EXPLORATION,
            self.target_id, self.target_version_at_submission,
            suggestion_models.STATUS_IN_REVIEW, 'author_2',
            'reviewer_2', self.change_cmd, 'category3',
            'exploration.exp1.thread_8')
        suggestion_models.GeneralSuggestionModel.create(
            suggestion_models.SUGGESTION_TYPE_EDIT_STATE_CONTENT,
            suggestion_models.TARGET_TYPE_EXPLORATION,
            self.target_id, self.target_version_at_submission,
            suggestion_models.STATUS_REJECTED, 'author_2',
            'reviewer_2', self.change_cmd, 'category1',
            'exploration.exp1.thread_9')
        suggestion_models.GeneralSuggestionModel.create(
            suggestion_models.SUGGESTION_TYPE_EDIT_STATE_CONTENT,
            suggestion_models.TARGET_TYPE_EXPLORATION,
            self.target_id, self.target_version_at_submission,
            suggestion_models.STATUS_IN_REVIEW, 'author_3',
            'reviewer_2', self.change_cmd, 'category2',
            'exploration.exp1.thread_10')

        self.assertEqual(len(
            suggestion_models.GeneralSuggestionModel
            .get_in_review_suggestions_in_score_categories(
                ['category1'], 'author_3')), 0)
        self.assertEqual(len(
            suggestion_models.GeneralSuggestionModel
            .get_in_review_suggestions_in_score_categories(
                ['category1'], 'author_2')), 1)
        self.assertEqual(len(
            suggestion_models.GeneralSuggestionModel
            .get_in_review_suggestions_in_score_categories(
                ['category2'], 'author_2')), 1)
        self.assertEqual(len(
            suggestion_models.GeneralSuggestionModel
            .get_in_review_suggestions_in_score_categories(
                ['category1', 'category2'], 'author_3')), 1)
        self.assertEqual(len(
            suggestion_models.GeneralSuggestionModel
            .get_in_review_suggestions_in_score_categories(
                ['category1', 'category2', 'category3'], 'author_1')), 4)
        self.assertEqual(len(
            suggestion_models.GeneralSuggestionModel
            .get_in_review_suggestions_in_score_categories(
                ['category1', 'category_invalid'], 'author_2')), 1)
        with self.assertRaisesRegexp(
            Exception, 'Received empty list of score categories'):
            self.assertEqual(len(
                suggestion_models.GeneralSuggestionModel
                .get_in_review_suggestions_in_score_categories(
                    [], 'author_1')), 0)

    def test_get_all_score_categories(self):
        suggestion_models.GeneralSuggestionModel.create(
            suggestion_models.SUGGESTION_TYPE_EDIT_STATE_CONTENT,
            suggestion_models.TARGET_TYPE_EXPLORATION,
            self.target_id, self.target_version_at_submission,
            suggestion_models.STATUS_IN_REVIEW, 'author_3',
            'reviewer_2', self.change_cmd, 'category1',
            'exploration.exp1.thread_11')
        suggestion_models.GeneralSuggestionModel.create(
            suggestion_models.SUGGESTION_TYPE_EDIT_STATE_CONTENT,
            suggestion_models.TARGET_TYPE_EXPLORATION,
            self.target_id, self.target_version_at_submission,
            suggestion_models.STATUS_REJECTED, 'author_3',
            'reviewer_2', self.change_cmd, 'category2',
            'exploration.exp1.thread_12')
        score_categories = (
            suggestion_models.GeneralSuggestionModel.get_all_score_categories())
        self.assertIn(self.score_category, score_categories)
        self.assertIn('category1', score_categories)
        self.assertIn('category2', score_categories)

    def test_export_data_trivial(self):
        user_data = (
            suggestion_models.GeneralSuggestionModel
            .export_data('non_existent_user'))
        test_data = {}
        self.assertEqual(user_data, test_data)

    def test_export_data_nontrivial(self):
        test_export_suggestion_type = (
            suggestion_models.SUGGESTION_TYPE_EDIT_STATE_CONTENT)
        test_export_target_type = suggestion_models.TARGET_TYPE_EXPLORATION
        test_export_target_id = self.target_id
        test_export_target_version = self.target_version_at_submission
        test_export_status = suggestion_models.STATUS_IN_REVIEW
        test_export_author = 'test_export_author'
        test_export_reviewer = 'test_export_reveiwer'
        test_export_change_cmd = self.change_cmd
        test_export_score_category = 'category1'
        test_export_thread_id = 'exploration.exp1.thread_export'

        suggestion_models.GeneralSuggestionModel.create(
            test_export_suggestion_type,
            test_export_target_type,
            test_export_target_id,
            test_export_target_version,
            test_export_status,
            test_export_author,
            test_export_reviewer,
            test_export_change_cmd,
            test_export_score_category,
            test_export_thread_id
        )

        user_data = (
            suggestion_models.GeneralSuggestionModel
            .export_data('test_export_author'))

        test_data = {
            test_export_thread_id: {
                'suggestion_type': test_export_suggestion_type,
                'target_type': test_export_target_type,
                'target_id': test_export_target_id,
                'target_version_at_submission': test_export_target_version,
                'status': test_export_status,
                'change_cmd': test_export_change_cmd
            }
        }

        self.assertEqual(user_data, test_data)
