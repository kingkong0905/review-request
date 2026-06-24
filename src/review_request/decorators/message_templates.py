"""Message templates for different types of notifications."""

from typing import List


class ReviewMessageTemplates:
    """Templates for pull request review messages."""

    TEMPLATES: List[str] = [
        "Hey team, could you help to review {user_mention}PR?\n"
        "<{pr_url}|[{repo_name}] {title}>\n"
        "{reviewers_section}"
        "Thanks so much for the support! {icon}",
        "Hey all, {user_mention}is looking for your awesome feedback on this PR: \n"
        "<{pr_url}|[{repo_name}] {title}>\n"
        "{reviewers_section}"
        "Could you help to review? Thanks in advance! {icon}",
        "Someone call the code police, {user_mention}pushed this PR: \n"
        "<{pr_url}|[{repo_name}] {title}>\n"
        "{reviewers_section}"
        "Can you help interrogate it with a review? {icon}",
        "Hey heroes, {user_mention}dropped this PR from the coding galaxy: \n"
        "<{pr_url}|[{repo_name}] {title}>\n"
        "{reviewers_section}"
        "Let's give it some Earthling feedback! {icon}",
        "Yo legends, {user_mention}uploaded some spicy code: \n"
        "<{pr_url}|[{repo_name}] {title}>\n"
        "{reviewers_section}"
        "Can we cool it down with your review? {icon}",
        "I love coding almost as much as I love when you review PRs {user_mention}dropped one here: \n"
        "<{pr_url}|[{repo_name}] {title}>\n"
        "{reviewers_section}"
        "Mind giving it a quick look? {icon}",
        "Hey team, I love coding but we love clean code more! {user_mention}has this PR: \n"
        "<{pr_url}|[{repo_name}] {title}>\n"
        "{reviewers_section}"
        "Help keep it tidy with your review? {icon}",
        "Ahoy mates! {user_mention}has set code adrift on the open sea: \n"
        "<{pr_url}|[{repo_name}] {title}>\n"
        "{reviewers_section}"
        "Might you lend your sharp eyes and offer a kind review? {icon}",
        "Good day, crew. A fine PR from {user_mention}awaits your wisdom: \n"
        "<{pr_url}|[{repo_name}] {title}>\n"
        "{reviewers_section}"
        "Let us chart its course together with your thoughtful review {icon}",
        "Captain {user_mention}has crafted a new code voyage: \n"
        "<{pr_url}|[{repo_name}] {title}>\n"
        "{reviewers_section}"
        "If you've a moment, your review would help keep us on course {icon}",
        "A treasure of a PR has surfaced, courtesy of {user_mention}has: \n"
        "<{pr_url}|[{repo_name}] {title}>\n"
        "{reviewers_section}"
        "Could you help us inspect it with care and kindness? {icon}",
        "Crew, {user_mention}brings forth a pull request of promise: \n"
        "<{pr_url}|[{repo_name}] {title}>\n"
        "{reviewers_section}"
        "Would you mind giving it a look before we hoist the sails? {icon}",
        "Smooth waters ahead, but only if this PR from {user_mention}is reviewed: \n"
        "<{pr_url}|[{repo_name}] {title}>\n"
        "{reviewers_section}"
        "A kind review from ye would be most appreciated {icon}",
        "A precious bit of code has been unearthed by {user_mention}has: \n"
        "<{pr_url}|[{repo_name}] {title}>\n"
        "{reviewers_section}"
        "Would you offer your review to help polish this gem? {icon}",
        "Avast, good crew! {user_mention}has left this PR on our shores: \n"
        "<{pr_url}|[{repo_name}] {title}>\n"
        "{reviewers_section}"
        "Care to take a stroll through the lines and share your thoughts? {icon}",
        "A new entry in the log from {user_mention}has been found: \n"
        "<{pr_url}|[{repo_name}] {title}>\n"
        "{reviewers_section}"
        "We'd be grateful if you could review this with your steady compass {icon}",
        "Gentlefolk of the code seas, {user_mention}latest pull bears promise: \n"
        "<{pr_url}|[{repo_name}] {title}>\n"
        "{reviewers_section}"
        "A kind review would help bring it to safe harbor {icon}",
        "{user_mention}has released code into the night:\n"
        "<{pr_url}|[{repo_name}] {title}>\n"
        "{reviewers_section}"
        "A review is the only thing standing between this and chaos {icon}",
        "{user_mention}has submitted a PR under the cover of night:\n"
        "<{pr_url}|[{repo_name}] {title}>\n"
        "{reviewers_section}"
        "Review requested. Clean code, clean city {icon}",
        "{user_mention}dropped a PR like a batarang in the dark:\n"
        "<{pr_url}|[{repo_name}] {title}>\n"
        "{reviewers_section}"
        "Target locked. Engage with review precision {icon}",
        "A line of code can change everything. {user_mention}knows this:\n"
        "<{pr_url}|[{repo_name}] {title}>\n"
        "{reviewers_section}"
        "One review could save production from the brink {icon}",
    ]


class SprintCompletionMessageTemplates:
    """Templates for sprint completion notifications."""

    TEMPLATE: str = (
        "🎉 *Sprint Completed!* 🎉\n\n"
        "📋 *Sprint:* {sprint_name}\n"
        "📅 *Start Date:* {start_date}\n"
        "📅 *End Date:* {end_date}\n"
        "👤 *Completed by:* {completed_by}\n\n"
        "Great job, team! Another sprint successfully completed! 🚀"
    )


class RemindReviewMessageTemplates:
    """Templates for reminder messages about pending reviews."""

    TEMPLATES: List[str] = [
        "Hey {team_mention}! 👋\n"
        "🐢 {total_pr} PRs are still waiting for review...\n"
        "They're growing older... wiser... and slightly passive-aggressive.\n"
        "Be a hero 🦸 — review them before they write their memoirs.\n",
        "Hey {team_mention}! 👋\n"
        "🧟 {total_pr} undead PRs are shambling through GitHub…\n"
        "Only your review can lay them to rest ⚰️",
        "Hey {team_mention}! 👋\n"
        "🐢 {total_pr} PRs moving at turtle speed…\n"
        "Speed them up with a lightning-fast review! ⚡",
        "Hey {team_mention}! 👋\n"
        "📦 {total_pr} PRs just chilling in review queue…\n"
        "They're starting to unionize. Please help. ✊",
        "Hey {team_mention}! 👋\n"
        "🐶 {total_pr} abandoned PRs looking for a forever reviewer ❤️\n"
        "Adopt one today. Be a good human.",
        "Hey {team_mention}! 👋\n"
        "⏳ {total_pr} PRs waiting longer than your morning coffee…\n"
        "Click fast before they spill over ☕",
        "Hey {team_mention}! 👋\n"
        "🧀 {total_pr} PRs aging like fine cheese…\n"
        "And not the good kind 🧼",
        "Hey {team_mention}! 👋\n"
        "🤖 {total_pr} PRs have become sentient…\n"
        "They demand feedback… or they will code themselves.",
        "Hey {team_mention}! 👋\n"
        "👻 {total_pr} ghost PRs haunting GitHub at night…\n"
        "Review them and break the curse 👻🔮",
        "Hey {team_mention}! 👋\n"
        "💅 {total_pr} PRs waiting for their moment\n"
        "Let's not keep them in wardrobe change forever 👗",
        "Hey {team_mention}! 👋\n"
        "🚀 {total_pr} PRs ready to launch…\n"
        "Just need your review fuel to take off 🚀",
    ]
