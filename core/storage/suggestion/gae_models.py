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

"""Models for Oppia suggestions."""
from __future__ import absolute_import  # pylint: disable=import-only-modules
from __future__ import unicode_literals  # pylint: disable=import-only-modules

import datetime

from core.platform import models
import feconf

from google.appengine.ext import ndb

(base_models,) = models.Registry.import_models([models.NAMES.base_model])

# Constants defining types of entities to which suggestions can be created.
TARGET_TYPE_EXPLORATION = 'exploration'
TARGET_TYPE_QUESTION = 'question'
TARGET_TYPE_SKILL = 'skill'
TARGET_TYPE_TOPIC = 'topic'

TARGET_TYPE_CHOICES = [
    TARGET_TYPE_EXPLORATION,
    TARGET_TYPE_QUESTION,
    TARGET_TYPE_SKILL,
    TARGET_TYPE_TOPIC
]

# Constants defining the different possible statuses of a suggestion.
STATUS_ACCEPTED = 'accepted'
STATUS_IN_REVIEW = 'review'
STATUS_REJECTED = 'rejected'

STATUS_CHOICES = [
    STATUS_ACCEPTED,
    STATUS_IN_REVIEW,
    STATUS_REJECTED
]

# Constants defining various suggestion types.
SUGGESTION_TYPE_EDIT_STATE_CONTENT = 'edit_exploration_state_content'
SUGGESTION_TYPE_TRANSLATE_CONTENT = 'translate_content'
SUGGESTION_TYPE_ADD_QUESTION = 'add_question'

SUGGESTION_TYPE_CHOICES = [
    SUGGESTION_TYPE_EDIT_STATE_CONTENT,
    SUGGESTION_TYPE_TRANSLATE_CONTENT,
    SUGGESTION_TYPE_ADD_QUESTION
]

# Defines what is the minimum role required to review suggestions
# of a particular type.
SUGGESTION_MINIMUM_ROLE_FOR_REVIEW = {
    SUGGESTION_TYPE_EDIT_STATE_CONTENT: feconf.ROLE_ID_EXPLORATION_EDITOR
}

# Constants defining various contribution types.
SCORE_TYPE_CONTENT = 'content'
SCORE_TYPE_TRANSLATION = 'translation'
SCORE_TYPE_QUESTION = 'question'

SCORE_TYPE_CHOICES = [
    SCORE_TYPE_CONTENT,
    SCORE_TYPE_TRANSLATION,
    SCORE_TYPE_QUESTION
]

# The delimiter to be used in score category field.
SCORE_CATEGORY_DELIMITER = '.'

ALLOWED_QUERY_FIELDS = ['suggestion_type', 'target_type', 'target_id',
                        'status', 'author_id', 'final_reviewer_id',
                        'score_category']

# Threshold number of days after which suggestion will be accepted.
THRESHOLD_DAYS_BEFORE_ACCEPT = 7

# Threshold time after which suggestion is considered stale and auto-accepted.
THRESHOLD_TIME_BEFORE_ACCEPT_IN_MSECS = (
    THRESHOLD_DAYS_BEFORE_ACCEPT * 24 * 60 * 60 * 1000)

# The default message to be shown when accepting stale suggestions.
DEFAULT_SUGGESTION_ACCEPT_MESSAGE = ('Automatically accepting suggestion after'
                                     ' %d days' % THRESHOLD_DAYS_BEFORE_ACCEPT)

# The amount to increase the score of the author by after successfuly getting an
# accepted suggestion.
INCREMENT_SCORE_OF_AUTHOR_BY = 1

# Action types for incoming requests to the suggestion action handlers.
ACTION_TYPE_ACCEPT = 'accept'
ACTION_TYPE_REJECT = 'reject'


class GeneralSuggestionModel(base_models.BaseModel):
    """Model to store suggestions made by Oppia users.

    The ID of the suggestions are created is the same as the ID of the thread
    linked to the suggestion.
    """

    # The type of suggestion.
    suggestion_type = ndb.StringProperty(
        required=True, indexed=True, choices=SUGGESTION_TYPE_CHOICES)
    # The type of the target entity which the suggestion is linked to.
    target_type = ndb.StringProperty(
        required=True, indexed=True, choices=TARGET_TYPE_CHOICES)
    # The ID of the target entity being suggested to.
    target_id = ndb.StringProperty(required=True, indexed=True)
    # The version number of the target entity at the time of creation of the
    # suggestion.
    target_version_at_submission = ndb.IntegerProperty(
        required=True, indexed=True)
    # Status of the suggestion.
    status = ndb.StringProperty(
        required=True, indexed=True, choices=STATUS_CHOICES)
    # The ID of the author of the suggestion.
    author_id = ndb.StringProperty(required=True, indexed=True)
    # The ID of the reviewer who accepted/rejected the suggestion.
    final_reviewer_id = ndb.StringProperty(indexed=True)
    # The change command linked to the suggestion. Contains the details of the
    # change.
    change_cmd = ndb.JsonProperty(required=True)
    # The category to score the suggestor in. This field will contain 2 values
    # separated by a ., the first will be a value from SCORE_TYPE_CHOICES and
    # the second will be the subcategory of the suggestion.
    score_category = ndb.StringProperty(required=True, indexed=True)

    @staticmethod
    def get_deletion_policy():
        """General suggestion needs to be pseudonymized for the user."""
        return base_models.DELETION_POLICY.LOCALLY_PSEUDONYMIZE

    @classmethod
    def has_reference_to_user_id(cls, user_id):
        """Check whether GeneralSuggestionModel exists for the user.

        Args:
            user_id: str. The ID of the user whose data should be checked.

        Returns:
            bool. Whether any models refer to the given user ID.
        """
        return cls.query(
            ndb.OR(cls.author_id == user_id, cls.final_reviewer_id == user_id)
        ).get() is not None

    @classmethod
    def create(
            cls, suggestion_type, target_type, target_id,
            target_version_at_submission, status, author_id,
            final_reviewer_id, change_cmd, score_category,
            thread_id):
        """Creates a new SuggestionModel entry.

        Args:
            suggestion_type: str. The type of the suggestion.
            target_type: str. The type of target entity being edited.
            target_id: str. The ID of the target entity being edited.
            target_version_at_submission: int. The version number of the target
                entity at the time of creation of the suggestion.
            status: str. The status of the suggestion.
            author_id: str. The ID of the user who submitted the suggestion.
            final_reviewer_id: str. The ID of the reviewer who has
                accepted/rejected the suggestion.
            change_cmd: dict. The actual content of the suggestion.
            score_category: str. The scoring category for the suggestion.
            thread_id: str. The ID of the feedback thread linked to the
                suggestion.

        Raises:
            Exception: There is already a suggestion with the given id.
        """
        instance_id = thread_id

        if cls.get_by_id(instance_id):
            raise Exception('There is already a suggestion with the given'
                            ' id: %s' % instance_id)

        cls(id=instance_id, suggestion_type=suggestion_type,
            target_type=target_type, target_id=target_id,
            target_version_at_submission=target_version_at_submission,
            status=status, author_id=author_id,
            final_reviewer_id=final_reviewer_id, change_cmd=change_cmd,
            score_category=score_category).put()

    @classmethod
    def query_suggestions(cls, query_fields_and_values):
        """Queries for suggestions.

        Args:
            query_fields_and_values: list(tuple(str, str)). A list of queries.
                The first element in each tuple is the field to be queried, and
                the second element is the corresponding value to query for.

        Returns:
            list(SuggestionModel). A list of suggestions that match the given
            query values, up to a maximum of feconf.DEFAULT_QUERY_LIMIT
            suggestions.
        """
        query = cls.query()
        for (field, value) in query_fields_and_values:
            if field not in ALLOWED_QUERY_FIELDS:
                raise Exception('Not allowed to query on field %s' % field)
            query = query.filter(getattr(cls, field) == value)

        return query.fetch(feconf.DEFAULT_QUERY_LIMIT)

    @classmethod
    def get_all_stale_suggestions(cls):
        """Gets all suggestions which were last updated before the threshold
        time.

        Returns:
            list(SuggestionModel). A list of suggestions that are stale.
        """
        threshold_time = (
            datetime.datetime.utcnow() - datetime.timedelta(
                0, 0, 0, THRESHOLD_TIME_BEFORE_ACCEPT_IN_MSECS))
        return cls.get_all().filter(cls.status == STATUS_IN_REVIEW).filter(
            cls.last_updated < threshold_time).fetch()

    @classmethod
    def get_in_review_suggestions_in_score_categories(
            cls, score_categories, user_id):
        """Gets all suggestions which are in review in the given
        score_categories.

        Args:
            score_categories: list(str). list of score categories to query for.
            user_id: list(str). The id of the user trying to make this query.
                As a user cannot review their own suggestions, suggestions
                authored by the user will be excluded.

        Returns:
            list(SuggestionModel). A list of suggestions that are in the given
                score categories, which are in review, but not created by the
                given user.
        """
        if len(score_categories) == 0:
            raise Exception('Received empty list of score categories')

        return cls.get_all().filter(cls.status == STATUS_IN_REVIEW).filter(
            cls.score_category.IN(score_categories)).filter(
                cls.author_id != user_id).fetch(
                    feconf.DEFAULT_QUERY_LIMIT)

    @classmethod
    def get_in_review_suggestions_of_suggestion_type(
            cls, suggestion_type, user_id):
        """Gets all suggestions of suggestion_type which are in review.

        Args:
            suggestion_type: str. The type of suggestion to query for.
            user_id: str. The id of the user trying to make this query.
                As a user cannot review their own suggestions, suggestions
                authored by the user will be excluded.

        Returns:
            list(SuggestionModel). A list of suggestions that are of the given
                type, which are in review, but not created by the given user.
        """
        return cls.get_all().filter(cls.status == STATUS_IN_REVIEW).filter(
            cls.suggestion_type == suggestion_type).filter(
                cls.author_id != user_id).fetch(feconf.DEFAULT_QUERY_LIMIT)

    @classmethod
    def get_user_created_suggestions_of_suggestion_type(
            cls, suggestion_type, user_id):
        """Gets all suggestions of suggestion_type which the user has created.

        Args:
            suggestion_type: str. The type of suggestion to query for.
            user_id: str. The id of the user trying to make this query.

        Returns:
            list(SuggestionModel). A list of suggestions that are of the given
                type, which the given user has created.
        """
        return cls.get_all().filter(cls.status == STATUS_IN_REVIEW).filter(
            cls.suggestion_type == suggestion_type).filter(
                cls.author_id == user_id).fetch(feconf.DEFAULT_QUERY_LIMIT)

    @classmethod
    def get_all_score_categories(cls):
        """Gets all the score categories for which suggestions have been
        created.

        Returns:
            list(str). A list of all the score categories.
        """
        query_set = cls.query(projection=['score_category'], distinct=True)
        return [data.score_category for data in query_set]

    @classmethod
    def export_data(cls, user_id):
        """Exports the data from GeneralSuggestionModel
        into dict format for Takeout.

        Args:
            user_id: str. The ID of the user whose data should be exported.

        Returns:
            dict. Dictionary of the data from GeneralSuggestionModel.
        """

        user_data = dict()
        suggestion_models = (
            cls.get_all()
            .filter(cls.author_id == user_id).fetch())

        for suggestion_model in suggestion_models:
            user_data[suggestion_model.id] = {
                'suggestion_type': suggestion_model.suggestion_type,
                'target_type': suggestion_model.target_type,
                'target_id': suggestion_model.target_id,
                'target_version_at_submission': (
                    suggestion_model
                    .target_version_at_submission),
                'status': suggestion_model.status,
                'change_cmd': suggestion_model.change_cmd,
            }

        return user_data
