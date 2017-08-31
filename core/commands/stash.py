from sublime_plugin import WindowCommand

from ..git_command import GitCommand
from ..ui_mixins.quick_panel import show_stash_panel
from ...common import util


class GsApplyStashCommand(WindowCommand, GitCommand):

    """
    Apply the selected stash.
    """

    def run(self, stash_id=None):
        if stash_id is None:
            show_stash_panel(self.do_apply)
        else:
            self.do_apply(stash_id)

    def do_apply(self, id):
        if id == -1:
            return

        self.apply_stash(id)
        util.view.refresh_gitsavvy(self.window.active_view())


class GsPopStashCommand(WindowCommand, GitCommand):

    """
    Pop the selected stash.
    """

    def run(self, stash_id=None):
        if stash_id is None:
            show_stash_panel(self.do_pop)
        else:
            self.do_pop(stash_id)

    def do_pop(self, id):
        if id == -1:
            return

        self.pop_stash(id)
        util.view.refresh_gitsavvy(self.window.active_view())


class GsShowStashCommand(WindowCommand, GitCommand):

    """
    For each selected stash, open a new window to display the diff
    for that stash.
    """

    def run(self, stash_ids=[]):
        if len(stash_ids) == 0:
            show_stash_panel(self.do_show)
        else:
            for stash_id in stash_ids:
                self.do_show(stash_id)

    def do_show(self, id):
        if id == -1:
            return

        stash_view = self.get_stash_view("stash@{{{}}}".format(id))
        stash_view.run_command("gs_replace_view_text", {"text": self.show_stash(id), "nuke_cursors": True})

    def get_stash_view(self, title):
        window = self.window if hasattr(self, "window") else self.view.window()
        repo_path = self.repo_path
        stash_view = util.view.get_scratch_view(self, "stash_" + title, read_only=True)
        stash_view.set_name(title)
        stash_view.set_syntax_file("Packages/GitSavvy/syntax/diff.sublime-syntax")
        stash_view.settings().set("git_savvy.repo_path", repo_path)
        window.focus_view(stash_view)
        stash_view.sel().clear()

        return stash_view


class GsCreateStashCommand(WindowCommand, GitCommand):

    """
    Create a new stash from the user's unstaged changes.
    """

    def run(self, include_untracked=False, stash_of_indexed=False):
        self.include_untracked = include_untracked
        self.stash_of_indexed = stash_of_indexed
        self.window.show_input_panel("Description:", "", self.on_done, None, None)

    def on_done(self, description):
        if not self.stash_of_indexed:
            self.create_stash(description, include_untracked=self.include_untracked)
        else:
            # Create a temporary stash of everything, including staged files.
            self.git("stash", "--keep-index")
            # Stash only the indexed files, since they're the only thing left in the working directory.
            self.create_stash(description)
            # Clean out the working directory.
            self.git("reset", "--hard")
            try:
                # Pop the original stash, taking us back to the original working state.
                self.apply_stash(1)
                # Get the diff from the originally staged files, and remove them from the working dir.
                stash_text = self.git("stash", "show", "--no-color", "-p")
                self.git("apply", "-R", stdin=stash_text)
                # Delete the temporary stash.
                self.drop_stash(1)
                # Remove all changes from the staging area.
                self.git("reset")
            except Exception as e:
                # Restore the original working state.
                self.pop_stash(1)
                raise e
        util.view.refresh_gitsavvy(self.window.active_view())


class GsDiscardStashCommand(WindowCommand, GitCommand):

    """
    Drop the selected stash.
    """

    def run(self, stash_id=None):
        if stash_id is None:
            show_stash_panel(self.do_drop)
        else:
            self.do_drop(stash_id)

    def do_drop(self, id):
        if id == -1:
            return

        @util.actions.destructive(description="discard a stash")
        def do_drop_stash(id):
            self.drop_stash(id)
        do_drop_stash(id)
