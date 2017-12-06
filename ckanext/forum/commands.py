from ckan.lib.cli import CkanCommand

import logging
import sys


class ForumCommand(CkanCommand):
    """
    Usage:

        paster forum init_db
           - Creates the database table forum needs to run
    """
    summary = __doc__.split('\n')[0]
    usage = __doc__

    def command(self):
        """
        Parse command line arguments and call appropriate method.
        """
        if not self.args or self.args[0] in ['--help', '-h', 'help']:
            print self.usage
            sys.exit(1)

        cmd = self.args[0]
        self._load_config()

        self.log = logging.getLogger(__name__)

        if cmd == 'init_db':
            from ckanext.forum.models import init_db
            init_db()
            self.log.info('Forum tables are initialized')
        else:
            self.log.error('Command %s not recognized' % (cmd,))
