# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.


import re
try:
    import cPickle as pickle
except ImportError:
    import pickle

from django import forms
from django.contrib.gis.db import models as djm


class FloatArrayFormField(forms.Field):
    """Form field for properly handling float arrays/lists."""

    #: regex for splitting string lists on whitespace or commas
    ARRAY_RE = re.compile('[\s,]+')

    def clean(self, value):
        """Try to coerce either a string list of values (separated by
        whitespace and/or commas or a list/tuple of values to a list of
        floats. If unsuccessful, raise a
        :exception:`django.forms.ValidationError`
        """
        if isinstance(value, (tuple, list)):
            try:
                value = [float(x) for x in value]
            except (TypeError, ValueError):
                raise forms.ValidationError(
                    'Could not coerce sequence values to `float` values'
                )
        elif isinstance(value, str):
            # it could be a string list, like this: "1, 2,3 , 4 5"
            # try to convert it to a an actual list of floats
            try:
                value = [float(x) for x in self.ARRAY_RE.split(value)]
            except ValueError:
                raise forms.ValidationError(
                    'Could not coerce `str` to a list of `float` values'
                )
        else:
            raise forms.ValidationError(
                'Could not convert value to `list` of `float` values: %s'
                % value
            )
        return value


class PickleFormField(forms.Field):
    """Form field for Python objects which are pickle and saved to the
    database."""

    def clean(self, value):
        """We assume that the Python value specified for this field is exactly
        what we want to pickle and save to the database.

        The value will not modified.
        """
        return value


class FloatArrayField(djm.Field):
    """This field models a postgres `float` array."""

    def db_type(self, connection):
        return 'float[]'

    def get_prep_value(self, value):
        if value is not None:
            return "{" + ', '.join(str(v) for v in value) + "}"
        else:
            return None

    def formfield(self, **kwargs):
        """Specify a custom form field type so forms know how to handle fields
        of this type.
        """
        defaults = {'form_class': FloatArrayFormField}
        defaults.update(kwargs)
        return super(FloatArrayField, self).formfield(**defaults)


class CharArrayField(djm.Field):
    """This field models a postgres `varchar` array."""

    def db_type(self, _connection):
        return 'varchar[]'

    def get_prep_value(self, value):
        """Return data in a format that has been prepared for use as a
        parameter in a query.

        :param value: sequence of string values to be saved in a varchar[]
            field
        :type value: list or tuple

        >>> caf = CharArrayField()
        >>> caf.get_prep_value(['foo', 'bar', 'baz123'])
        '{"foo", "bar", "baz123"}'
        """
        if value is not None:
            return '{' + ', '.join('"%s"' % str(v) for v in value) + '}'
        else:
            return None


class PickleField(djm.Field):
    """Field for transparent pickling and unpickling of python objects."""

    __metaclass__ = djm.SubfieldBase

    SUPPORTED_BACKENDS = set((
        'django.contrib.gis.db.backends.postgis',
        'django.db.backends.postgresql_psycopg2'
    ))

    def db_type(self, connection):
        """Return "bytea" as postgres' column type."""
        assert connection.settings_dict['ENGINE'] in self.SUPPORTED_BACKENDS
        return 'bytea'

    def to_python(self, value):
        """Unpickle the value."""
        if value and isinstance(value, (buffer, str, bytearray)):
            return pickle.loads(str(value))
        else:
            return value

    def get_prep_value(self, value):
        """Pickle the value."""
        return bytearray(pickle.dumps(value, pickle.HIGHEST_PROTOCOL))

    def formfield(self, **kwargs):
        """Specify a custom form field type so forms don't treat this as a
        default type (such as a string). Any Python object is valid for this
        field type.
        """
        defaults = {'form_class': PickleFormField}
        defaults.update(kwargs)
        return super(PickleField, self).formfield(**defaults)


