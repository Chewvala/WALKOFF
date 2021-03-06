import xml.etree.cElementTree as et

from jinja2 import Template

from core import config


class Argument(object):
    def __init__(self, key=None, value=None, format="str"):
        self.key = key
        self.value = value
        self.templated = None
        self.format = format
        self.value = self.convertTo(value=self.value, type=self.format)

    def __call__(self):
        if self.templated:
            return self.templated
        return self.value

    def convertTo(self, value=None, type="str"):
        output = value
        if any(type == string_type for string_type in ['str', 'string', 'unicode']):
            try:
                output = str(output)
            except ValueError:
                return output
        elif type == "int":
            try:
                output = int(output)
            except ValueError as e:
                return output
        return output

    def template(self, **kwargs):
        template = Template(str(self.value))
        self.templated = template.render(config.JINJA_GLOBALS, **kwargs)
        return self.templated

    def to_xml(self):
        elem = et.Element(self.key)
        elem.text = str(self.value)
        elem.set("format", self.format)
        return elem

    def __repr__(self):
        output = {'key': self.key,
                  'value': str(self.value),
                  'type': self.format}
        return str(output)

    def validate(self, action=None, io="input"):
        for x in config.functionConfig[action]["args"]:
            if x["type"] != self.format:
                try:
                    self.value = self.convertTo(value=self.value, type=x["type"])
                except:
                    return False
        return any(x["name"] == self.key and x["type"] == self.format for x in config.functionConfig[action]["args"])

    def as_json(self):
        return {"key": str(self.key),
                "value": str(self.value),
                "format": str(self.format)}
