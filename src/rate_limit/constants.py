__author__ = 'sanjeev'

from djchoices import DjangoChoices, ChoiceItem


class SpecializationType(DjangoChoices):
    GLOBAL = ChoiceItem(value='GLOBAL', label="GLOBAL")
    METHOD = ChoiceItem(value='METHOD', label="METHOD")
    API = ChoiceItem(value='API', label="API")
