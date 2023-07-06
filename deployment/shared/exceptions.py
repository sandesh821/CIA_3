#Copyright (c) Microsoft. All rights reserved.
#The custom error classes are derived from super class Exception
class EmptyInputfileError(Exception):
    def __init__(self):
        self.errcode =100
        self.errtype = "Bad input file Error"
        self.errmsg = "Input file is empty"


class NonUniqueTimeStampError(Exception):
    def __init__(self):
        self.errcode =100
        self.errtype = "Bad input file Error"
        self.errmsg = "Unique timestamp not available"

class PiTagMissmatchError(Exception):
    def __init__(self):
        self.errcode =100
        self.errtype = "Bad input file Error"
        self.errmsg = "Pi Tag count mismatch"

class NonNumericValueError(Exception):
    def __init__(self):
        self.errcode =100
        self.errtype = "Bad input file Error"
        self.errmsg = "Contains non-numeric/null values"

class SQLDataLoadError(Exception):
    def __init__(self, message):
        self.errcode =101
        self.errtype = "SQL DB Data Load Error"
        self.errmsg = message

class FileMovementError(Exception):
    def __init__(self, message):
        self.errcode =102
        self.errtype = "File Movement Error"
        self.errmsg = message

class ModelScoringError(Exception):
    def __init__(self, message):
        self.errcode =103
        self.errtype = "Model Scoring Error"
        self.errmsg = message