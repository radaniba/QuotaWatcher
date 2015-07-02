#!/usr/bin/env python2
# -*- coding: utf8 -*-

"""
    quotawatcher.py: Monitors changes in the size of dirs for a given path
"""

# ==============================================================================
# This Script monitors the changes in disk size for the directories included in
# a given path. It reports directories with a size exceeding a threshold specified
# by the user, here we use 2 Terabytes
# The final report is sent via email to a list of email addresses usually of the users to monitor their disk usage.
# This script is intended to run periodically (e.g. via cron)
# ==============================================================================

# ==============================================================================
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
# ==============================================================================
from __future__ import division

__author__ = "Rad <aradwen@gmail.com>"
__license__ = "GNU General Public License version 3"
__date__ = "06/30/2015"
__version__ = "0.2"

try:
    import os
    from quota_logger import init_log
    import subprocess
    from prettytable import PrettyTable
    from smtplib import SMTP
    from smtplib import SMTPException
    from email.mime.text import MIMEText
    from argparse import ArgumentParser
except ImportError:
    # Checks the installation of the necessary python modules
    import os
    import sys

    print((os.linesep * 2).join(
        ["An error found importing one module:", str(sys.exc_info()[1]), "You need to install it Stopping..."]))
    sys.exit(-2)


class Notifier(object):

    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']

    def __init__(self, **kwargs):

        self.threshold = None
        self.path = None
        self.list = None
        self.email_sender = None
        self.email_password = None
        self.gmail_smtp = None
        self.gmail_smtp_port = None
        self.text_subtype = None
        self.cap_reached = False
        self.email_subject = None

        for (key, value) in kwargs.iteritems():
            if hasattr(self, key):
                setattr(self, key, value)

        self._log = init_log()

    @property
    def loggy(self):
        return self._log

    @staticmethod
    def load_recipients_emails(emails_file):
        recipients = [line.rstrip('\n') for line in open(emails_file) if not line[0].isspace()]
        return recipients

    @staticmethod
    def load_message_content(message_template_file, table):
        template_file = open(message_template_file, 'rb')
        template_file_content = template_file.read().replace(
            "{{table}}", table.get_string())
        template_file.close()
        return template_file_content

    def notify_user(self, email_receivers, table, template):
        """This method sends an email
        :rtype : email sent to specified members
        """
        # Create the message
        input_file = os.path.join(
            os.path.dirname(__file__), "templates/" + template + ".txt")
        content = self.load_message_content(input_file, table)

        msg = MIMEText(content, self.text_subtype)

        msg["Subject"] = self.email_subject
        msg["From"] = self.email_sender
        msg["To"] = ','.join(email_receivers)

        try:
            smtpObj = SMTP(self.gmail_smtp, self.gmail_smtp_port)
            # Identify yourself to GMAIL ESMTP server.
            smtpObj.ehlo()
            # Put SMTP connection in TLS mode and call ehlo again.
            smtpObj.starttls()
            smtpObj.ehlo()
            # Login to service
            smtpObj.login(user=self.email_sender, password=self.email_password)
            # Send email
            smtpObj.sendmail(self.email_sender, email_receivers, msg.as_string())
            # close connection and session.
            smtpObj.quit()
        except SMTPException as error:
            print "Error: unable to send email :  {err}".format(err=error)

    @staticmethod
    def du(path):
        """disk usage in kilobytes"""
        # return subprocess.check_output(['du', '-s',
        # path]).split()[0].decode('utf-8')
        try:
            p1 = subprocess.Popen(('ls', '-d', path), stdout=subprocess.PIPE)
            p2 = subprocess.Popen((os.environ["GNU_PARALLEL"], '--no-notice', 'du', '-s', '2>&1'), stdin=p1.stdout,
                                  stdout=subprocess.PIPE)
            p3 = subprocess.Popen(
                ('grep', '-v', '"Permission denied"'), stdin=p2.stdout, stdout=subprocess.PIPE)
            output = p3.communicate()[0]
        except subprocess.CalledProcessError as e:
            raise RuntimeError("command '{0}' return with error (code {1}): {2}".format(
                e.cmd, e.returncode, e.output))
        # return ''.join([' '.join(hit.split('\t')) for hit in output.split('\n')
        # if len(hit) > 0 and not "Permission" in hit and output[0].isdigit()])
        result = [' '.join(hit.split('\t')) for hit in output.split('\n')]
        for line in result:
            if line and len(line.split('\n')) > 0 and "Permission" not in line and line[0].isdigit():
                return line.split(" ")[0]

    def du_h(self, nbytes):
        if nbytes == 0:
            return '0 B'
        i = 0
        while nbytes >= 1024 and i < len(self.suffixes) - 1:
            nbytes /= 1024.
            i += 1
        f = ('%.2f'.format(nbytes)).rstrip('0').rstrip('.')
        return '%s %s'.format(f, self.suffixes[i])

    @staticmethod
    def list_folders(given_path):
        user_list = []
        for path in os.listdir(given_path):
            if not os.path.isfile(os.path.join(given_path, path)) and not path.startswith(".") and not path.startswith(
                    "archive"):
                user_list.append(path)
        return user_list

    def notify(self):
        global cap_reached
        self._log.info("Loading recipient emails...")
        list_of_recievers = self.load_recipients_emails(self.list)
        paths = self.list_folders(self.path)
        paths = [self.path + user for user in paths]
        sizes = []
        for size in paths:
            try:
                self._log.info("calculating disk usage for " + size + " ...")
                sizes.append(int(self.du(size)))
            except Exception, e:
                self._log.exception(e)
                sizes.append(0)
        # sizes = [int(du(size).split(' ')[0]) for size in paths]
        # convert kilobytes to bytes
        sizes = [int(element) * 1000 for element in sizes]
        table = PrettyTable(["Directory", "Size"])
        table.align["Directory"] = "l"
        table.align["Size"] = "r"
        table.padding_width = 5
        table.border = False
        for account, size_of_account in zip(paths, sizes):
            if int(size_of_account) > int(self.threshold):
                table.add_row(
                    ["*" + os.path.basename(account) + "*", "*" + self.du_h(size_of_account) + "*"])
                self.cap_reached = True
            else:
                table.add_row([os.path.basename(account), self.du_h(size_of_account)])
        # notify Admins
        table.add_row(["TOTAL", self.du_h(sum(sizes))])
        table.add_row(["Usage", str(sum(sizes) / 70000000000000)])
        self.notify_user(list_of_recievers, table, "karey")
        if self.cap_reached:
            self.notify_user(list_of_recievers, table, "default_size_limit")

    def run(self):
        self.notify()


def arguments():
    """Defines the command line arguments for the script."""
    main_desc = """Monitors changes in the size of dirs for a given path"""

    parser = ArgumentParser(description=main_desc)
    parser.add_argument("path", default=os.path.expanduser('~'), nargs='?',
                        help="The path to monitor. If none is given, takes the  home directory")
    parser.add_argument("list", help="text file containing the list of persons to be notified, one per line")
    parser.add_argument("-s", "--notification_subject", default=None, help="Email subject of the notification")
    parser.add_argument("-t", "--threshold", default=2500000000000,
                        help="The threshold that will trigger the notification")
    parser.add_argument("-v", "--version", action="version",
                        version="%(prog)s {0}".format(__version__),
                        help="show program's version number and exit")
    return parser


def main():

    args = arguments().parse_args()
    notifier = Notifier()
    loggy = notifier.loggy
    # Set parameters
    loggy.info("Starting QuotaWatcher session...")
    loggy.info("Setting parameters ...")
    notifier.list = args.list
    notifier.threshold = args.threshold
    notifier.path = args.path

    # Configure the app
    try:
        loggy.info("Loading environment variables ...")
        notifier.email_sender = os.environ["NOTIFIER_SENDER"]
        notifier.email_password = os.environ["NOTIFIER_PASSWD"]
        notifier.gmail_smtp = os.environ["NOTIFIER_SMTP"]
        notifier.gmail_smtp_port = os.environ["NOTIFIER_SMTP_PORT"]
        notifier.text_subtype = os.environ["NOTIFIER_SUBTYPE"]
        notifier.email_subject = args.notification_subject
        notifier.cap_reached = False
    except Exception, e:
        loggy.exception(e)

    notifier.run()
    loggy.info("End of QuotaWatcher session")


if __name__ == "__main__":
    main()
