#!/usr/bin/env python

import subprocess

import urwid

from util import clear_screen
from task import TaskCommand, TaskListModel
from report import TaskTable, SelectableRow, TaskListBox

PALETTE = [
    ('list-header', 'black', 'white'),
    ('reveal focus', 'black', 'dark cyan', 'standout'),
]

class Application():
    def __init__(self, task_config, reports, report):

        self.config = task_config
        self.reports = reports
        self.report = report
        self.command = TaskCommand()
        self.run(self.report)

    def key_pressed(self, key):
        if key in ('q', 'Q', 'esc'):
            raise urwid.ExitMainLoop()

    def on_select(self, row, size, key):
        if key == 'e':
            self.loop.stop()
            self.command.result(["task", row.uuid, "edit"])
            self.update_report()
            self.loop.start()
            key = None
        elif key == 'enter':
            self.loop.stop()
            self.command.result(["task", row.uuid, "info"])
            self.loop.start()
            key = None
        return key

    def build_report(self):
        self.model = TaskListModel(self.config, self.reports, self.report)
        self.table = TaskTable(self.config, self.reports[self.report], self.model.tasks, on_select=self.on_select)

        self.header = urwid.Pile([
            urwid.Text('Welcome to PYT'),
            self.table.header,
        ])
        self.footer = urwid.Text('Status: ready')

    def update_report(self, report=None):
        self.build_main_widget(report)
        self.loop.widget = self.widget

    def build_main_widget(self, report=None):
        if report:
            self.report = report
        self.build_report()
        self.widget = urwid.Frame(
            self.table.listbox,
            header=self.header,
            footer=self.footer,
        )

    def run(self, report):
        self.build_main_widget(report)
        self.loop = urwid.MainLoop(self.widget, PALETTE, unhandled_input=self.key_pressed)
        self.loop.run()
