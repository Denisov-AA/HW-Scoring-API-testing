import datetime
import functools
import unittest

import fakeredis

import src.api as api
from src.store import Storage, Store


def cases(cases):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args):
            new_args = None
            for c in cases:
                try:
                    new_args = args + (c if isinstance(c, tuple) else (c,))
                    f(*new_args)
                except Exception as e:
                    print(str(e), new_args)
                    raise

        return wrapper

    return decorator


class TestCharField(unittest.TestCase):

    @cases(["", "string", "\r\n"])
    def test_valid(self, value):
        self.assertIsNone(api.CharField().validate(value))

    @cases(
        [1, None, {"I am": "a dict"}, {"I", "am", "a", "set"}, ["I", "am", "a", "list"]]
    )
    def test_invalid(self, value):
        field = api.CharField()
        self.assertRaises(api.ValidationError, field.validate, value)


class TestArgumentsField(unittest.TestCase):

    @cases([dict(), {"I am": "a dict"}])
    def test_valid(self, value):
        self.assertIsNone(api.ArgumentsField().validate(value))

    @cases(
        [1, None, "I am a string", {"I", "am", "a", "set"}, ["I", "am", "a", "list"]]
    )
    def test_invalid(self, value):
        field = api.ArgumentsField()
        self.assertRaises(api.ValidationError, field.validate, value)


class TestEmailField(unittest.TestCase):

    @cases(["asergeenko@mail.ru", "@", "mymail@m.com"])
    def test_valid(self, value):
        self.assertIsNone(api.EmailField().validate(value))

    @cases(["", None, 111, {"email@email.com"}])
    def test_invalid(self, value):
        field = api.EmailField()
        self.assertRaises(api.ValidationError, field.validate, value)


class TestPhoneField(unittest.TestCase):

    @cases(["79991237733", 79035151234, 70000000000, ""])
    def test_valid(self, value):
        self.assertIsNone(api.PhoneField().validate(value))

    @cases(["779991237733", [79991237733], "+73469431234"])
    def test_invalid(self, value):
        field = api.PhoneField()
        self.assertRaises(api.ValidationError, field.validate, value)


class TestDateField(unittest.TestCase):

    def test_empty(self):
        self.assertIsNone(api.DateField().validate(""))

    def test_valid(self):
        self.assertEqual(
            api.DateField().validate("01.01.1971"),
            datetime.date(day=1, month=1, year=1971),
        )
        self.assertEqual(
            api.DateField().validate("18.11.2019"),
            datetime.date(day=18, month=11, year=2019),
        )
        self.assertEqual(
            api.DateField().validate("15.01.2016"),
            datetime.date(day=15, month=1, year=2016),
        )

    @cases(["1997.11.03", "01.01.1971 12:20:33", datetime.date.today()])
    def test_invalid(self, value):
        field = api.DateField()
        self.assertRaises(api.ValidationError, field.validate, value)


class TestBirthdayField(unittest.TestCase):

    def test_empty(self):
        self.assertIsNone(api.BirthDayField().validate(""))

    @cases(["8.8.2008", "01.01.2000", "12.04.2020"])
    def test_valid(self, value):
        self.assertIsNone(api.BirthDayField().validate(""))

    @cases(["2000.11.03", "01.01.1890", "12.07.1861"])
    def test_invalid(self, value):
        field = api.BirthDayField()
        self.assertRaises(api.ValidationError, field.validate, value)


class TestGenderField(unittest.TestCase):

    @cases(list(api.GENDERS.keys()))
    def test_valid(self, value):
        self.assertIsNone(api.GenderField().validate(value))

    @cases([100, "", 3.14, -300])
    def test_invalid(self, value):
        field = api.GenderField()
        self.assertRaises(api.ValidationError, field.validate, value)


class TestClientIDsField(unittest.TestCase):

    @cases([[1, 2, 3, 4, 5], [-1, -2, -3], [0], []])
    def test_valid(self, value):
        self.assertIsNone(api.ClientIDsField().validate(value))

    @cases(["+79991237733", [3.14, 2.71], 83469431234])
    def test_invalid(self, value):
        field = api.ClientIDsField()
        self.assertRaises(api.ValidationError, field.validate, value)


class TestStore(unittest.TestCase):

    def setUp(self):
        self.store = Store(Storage())
        self.store.storage.connect()
        self.server = fakeredis.FakeServer()
        self.store.storage.server = fakeredis.FakeRedis(server=self.server)
        self.store.set("foo", "bar")

    def test_get(self):
        self.server.connected = True
        self.assertEqual(self.store.get("foo"), "bar")
        self.assertIsNone(self.store.get("wow"))
        self.store.cache_set("foo", "not_bar")
        self.assertEqual(self.store.get("foo"), "not_bar")
        self.server.connected = False
        self.assertRaises(ConnectionError, self.store.get, "foo", False)

    def test_cache_get(self):
        self.assertEqual(self.store.cache_get("foo"), "bar")

    def test_connection_failed(self):
        self.server.connected = False
        self.assertRaises(ConnectionError, self.store.get, "foo", False)

    def test_connection_ok(self):
        self.server.connected = True
        self.assertEqual(self.store.get("foo"), "bar", False)


if __name__ == "__main__":
    unittest.main()
