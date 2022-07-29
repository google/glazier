# Error Codes

<!--* freshness: { owner: '@tseknet' reviewed: '2022-01-05' } *-->

The question of how to implement error codes has already been answered a
plethora of ways. An example is how Microsoft uses BSOD codes to identify fatal
failures with the Windows Operating System. Leveraging the same philosophy,
error codes should be added to all exceptions thrown by Glazier. There is a
difference between error codes and error return values. An error code gives a
user actionable feedback. An error return value is a coding technique to
indicate that your code has encountered an error.

## Background

For simplicity, Glazier error codes are all four digit numbers that follow the
pattern 7XXX. If no status code is defined by the error, the default (7000) will
be used.

Error codes achieve the following objectives:

1.  Convey the error code.
1.  Provide short*, actionable log messages.
1.  Documentation explaining error codes is a living document and can be updated
    as necessary.
1.  Data can be inferred based on the error code itself with where the issue
    originates (e.g. 7060 could relay information about not receiving an NTP
    response)

\* Having short status codes is essential since every exception will have this
string appended to it. The aim is to give the end consumer concise and
actionable steps for troubleshooting most known errors.

## Error Code Reference

Always refer to
[`errors.py`](https://github.com/google/glazier/blob/master/glazier/glazier/lib/errors.py)
for the most up-to-date error code values. All critical error codes should be
added to that library, rather than individual libraries. The expectation is
error codes point to anchors in your internal documentation.

## Defining Fatal Errors

The below pattern should be used when defining and raising any custom
`Exception`, in order to ensure details are logged appropriately. In this
example, we'll be introducing a new module, `division.py`.

```python
# In errors.py:

@enum.unique
class ErrorCode(enum.IntEnum):
  DEFAULT = 7000
  ...
  DIVIDE_BY_ZERO_ERROR = 7999  # Our new error code.
```

```python
# In division.py:

from glazier.lib import errors

class Error(errors.GlazierError):
  """Base class for all Exceptions in division.py."""
  pass

class DivideByZeroError(Error):

  def __init__(self, numerator: int, denominator: int):
    super().__init__(
        error_code=errors.ErrorCode.DIVIDE_BY_ZERO_ERROR,
        message=f'You tried to divide {numerator} by {denominator}')

def VeryBadCode():
  a = 1
  b = 0
  try:
    a / b
  except ZeroDivisionError as e:
    raise DivideByZeroError(a, b) from e  # Use raise/from whenever possible.
```

In this example, the error message will be as follows:

> You tried to divide 1 by 0 (Error Code: 7999) (Cause: division by zero)

NOTE: When raising a custom `GlazierError` subclass (in this example,
`DivideByZeroError`), it behooves you to raise that `Exception` using Python's
`raise from` syntax. The reason for this is that `GlazierError` will include the
root-cause message (in this example, "division by zero") along with whatever
custom error message you define.

Once this exception is caught by `autobuild.py`, the following log message will
be displayed:

```
***** IMAGING PROCESS FAILED *****

* Root Cause: You tried to divide 1 by 0 (Error Code: 7999)

* Location: <file.py>:<lineno>

* Logs: /Logs/glazier.log

* Troubleshooting: https://glazier-failures.example.com#7999
```
