import re
import urwid
# TODO: This isn't implemented in Python < 2.7.
from functools import cmp_to_key

from color_mappings import task_256_to_urwid_256, task_bright_to_color

COLORABLE_COLUMNS = [
    'depends',
    'description',
    'due',
    'project',
    'recur',
    'scheduled',
    'start',
    'status',
    'tag',
    # TODO: Will this one work correctly?
    'uda',
]
VALID_COLOR_MODIFIERS = [
    'bold',
    'underline',
]

class TaskColorizer(object):
    """Colorized task output.
    """
    def __init__(self, config, task_config):
        self.config = config
        self.task_config = task_config
        self.include_subprojects = self.config.get('color', 'include_subprojects')
        self.colorable_columns = COLORABLE_COLUMNS
        self.task_256_to_urwid_256 = task_256_to_urwid_256()
        self.color_enabled = self.task_config.subtree('color$', walk_subtree=False)['color'] == 'on'
        self.display_attrs_available, self.display_attrs = self.convert_color_config(self.task_config.filter_to_dict('^color\.'))
        self.project_display_attrs = self.get_project_display_attrs()
        self.color_precedence = self.task_config.subtree('rule.')['precedence']['color'].split(',')
        if self.include_subprojects:
            self.add_project_children()

    def add_project_children(self):
        color_prefix = 'color.project.'
        for (display_attr, fg16, bg16, m, fg256, bg256) in self.project_display_attrs:
            for entry in self.task_config.projects:
                attr = '%s%s' % (color_prefix, entry)
                if not self.has_display_attr(attr) and attr.startswith('%s.' % display_attr):
                    self.display_attrs_available[attr] = True
                    self.display_attrs.append((attr, fg16, bg16, m, fg256, bg256))

    def has_display_attr(self, display_attr):
        return display_attr in self.display_attrs_available and self.display_attrs_available[display_attr]

    def get_project_display_attrs(self):
        return sorted([(a, fg16, bg16, m, fg256, bg256) for (a, fg16, bg16, m, fg256, bg256) in self.display_attrs if self.display_attrs_available[a] and self.is_project_display_attr(a)], reverse=True)

    def is_project_display_attr(self, display_attr):
        return display_attr[0:14] == 'color.project.'

    def convert_color_config(self, color_config):
        display_attrs_available = {}
        display_attrs = []
        for key, value in color_config.items():
            foreground, background = self.convert_colors(value)
            available = self.has_color_config(foreground, background)
            display_attrs_available[key] = available
            if available:
                display_attrs.append(self.make_display_attr(key, foreground, background))
        return display_attrs_available, display_attrs

    def make_display_attr(self, display_attr, foreground, background):
        # TODO: Non-standard colors need to be translated down to standard.
        # TODO: Why aren't 256 colors being used when no basic colors are
        # provided?
        return (display_attr, foreground, background, '', foreground, background)

    def has_color_config(self, foreground, background):
        return foreground != '' or background != ''

    def convert_colors(self, color_config):
        # TODO: Maybe a fancy regex eventually...
        color_config = task_bright_to_color(color_config).strip()
        starts_with_on = color_config[0:3] == 'on '
        parts = list(map(lambda p: p.strip(), color_config.split('on ')))
        foreground, background = (parts[0], parts[1]) if len(parts) > 1 else (None, parts[0]) if starts_with_on else (parts[0], None)
        foreground_parts, background_parts = self.check_invert_color_parts(foreground, background)
        return self.convert(foreground_parts), self.convert(background_parts)

    # TODO: Better method name please...
    def convert(self, color_parts):
        sorted_parts = self.sort_color_parts(color_parts)
        remapped_colors = self.map_named_colors(sorted_parts)
        return ','.join(remapped_colors)

    def map_named_colors(self, color_parts):
        if len(color_parts) > 0 and color_parts[0] in self.task_256_to_urwid_256:
            color_parts[0] = self.task_256_to_urwid_256[color_parts[0]]
        return color_parts

    def check_invert_color_parts(self, foreground, background):
        foreground_parts = self.split_color_parts(foreground)
        background_parts = self.split_color_parts(background)
        inverse = False
        if 'inverse' in foreground_parts:
            foreground_parts.remove('inverse')
            inverse = True
        if 'inverse' in background_parts:
            background_parts.remove('inverse')
            inverse = True
        if inverse:
            return background_parts, foreground_parts
        else:
            return foreground_parts, background_parts

    def split_color_parts(self, color_parts):
        parts = color_parts.split() if color_parts else []
        return parts

    def is_modifier(self, elem):
        return elem in VALID_COLOR_MODIFIERS

    def sort_color_parts(self, color_parts):
        def comparator(first, second):
            if self.is_modifier(first) and not self.is_modifier(second):
                return 1
            elif not self.is_modifier(first) and self.is_modifier(second):
                return -1
            else:
                return 0
        return sorted(color_parts, key=cmp_to_key(comparator))
