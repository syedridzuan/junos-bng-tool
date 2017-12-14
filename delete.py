#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""Class to delete subscriber.

Common class to delete subscriber.
And verify deletion of the subscriber.

"""


class DeleteSubscriber:
    """Delete subscriber class."""

    def __init__(self, dev):
        """Init method. pass device."""
        self.dev = dev
        self.sub_int = None
        self.session_id = None

    def set_subsriber(self, sub_int=None, session_id=None):
        """Set sub_int and session_id."""
        if sub_int:
            self.sub_int = sub_int
            self.session_id = None
        elif session_id:
            self.session_id = session_id
            self.sub_int = None

    def delete_interface(self):
        """Clear pppoe using interface e.g.: clear pppoe sessions pp0.1."""
        command = "clear pppoe sessions {}".format(self.sub_int)
        result = self.dev.cli(command,
                              format='text',
                              warning=False)
        return result

    def clear_session(self, session_id):
        """command: clear services subscriber sessions client-id 1."""
        self.session_id = session_id
        command = ("clear services subscriber sessions client-id {}"
                   .format(self.session_id))
        result = self.dev.cli(command, format='text', warning=False)
        return result

    def verify_delete(self):
        """To verify subscriber deletion."""
        if self.sub_int:
            pass
        elif self.session_id:
            pass
        pass
