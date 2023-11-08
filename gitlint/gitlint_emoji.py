"""Gitlint extra rule definition."""

from __future__ import unicode_literals

import re

import requests

from gitlint.rules import CommitMessageTitle, LineRule, RuleViolation


class GitmojiTitle(LineRule):
    """Gitmoji title rule.

    This rule will enforce that each commit title is of the form
    "<gitmoji>(<scope>) <subject>" where gitmoji is an emoji from the list
    defined in https://gitmoji.carloscuesta.me and subject should be all
    lowercase
    """

    id = "UC1"
    name = "title-should-have-gitmoji-and-scope"
    target = CommitMessageTitle

    def validate(self, title, _commit):
        """Validate Gitmoji title rule.

        Downloads the list possible gitmojis from the project's GitHub
        repository and check that title contains one of them.
        """
        gitmojis = requests.get(
            "https://raw.githubusercontent.com/carloscuesta/gitmoji/master/packages/gitmojis/src/gitmojis.json",
            timeout=5,
        ).json()["gitmojis"]
        emojis = [item["emoji"] for item in gitmojis]
        pattern = r"^({:s})\(.*\)\s[a-z].*$".format("|".join(emojis))
        if not re.search(pattern, title):
            violation_msg = 'Title does not match regex "<gitmoji>(<scope>) <subject>"'
            return [RuleViolation(self.id, violation_msg, title)]
