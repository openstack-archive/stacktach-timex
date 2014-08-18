timex
=====

A time expressions library implementing a mini-language for manipulating
datetimes.

Much like regular expressions provide a mini-language for performing certain
operation on strings, Timex's time expressions provide a convenient way of
expressing datetime and date-range operations. These expressions are strings,
and can be safely read from a config file or user input.

A simple example: Say you are writing code that creates a report on phone calls
to a store. You have a call log, perhaps in a database, with a timestamp for
each call, and you need to keep separate counts of calls that happened during
"employee hours", i.e. when employees should be there to answer the phone.
Current policy is that those are 30min before opening til an hour after closing.
That policy may change, however, so you don't want to hardcode it.
Here is code that will get you what you need:

```python

import timex

# store_open and store_close are datetimes for a specific day.
# calls is a list of object with a .timestamp attribute, that is also a
#   datetime.
def count_calls(calls, store_open, store_close):
    count = 0

    # This expression string could come from a config file.
    time_expression = timex.parse("$opening - 30m to $closing + 1h")

    # Call a compiled expression with keyword args to substitute needed
    # variables.
    matcher = time_expression(opening=store_open, closing=store_close)

    for call in calls:
        # Time matchers returned by calling an expression override the
        # 'in' operator.
        if call.timestamp in matcher:
            count += 1
    return count

```

Another example: Calculating expiration dates.
Say you need to calculate expiration dates for some items. There are several
types, and each has different rules:

```python

import timex
from datetime import datetime

# These rules could be in a database table or config file.
EXPIRATION_RULES = {
    # This one expires at the beginning of the next day.
    "thingy_type": "($timestamp + 1d) @ 0h 0m 0s",
    # This one is only good for 3 hours
    'whatzit_type': "$timestamp + 3h",
    # Expires at noon on Dec, 31 of this year.
    'foobar_type': "$timestamp @ 12mo 31d 12h 0m 0s"
}

def set_expiration(items):
    for item in items:
        rule = EXPIRATION_RULES[item.type]

        # In real code, you'd probably compile the rules outside the
        # loop. It is fairly quick, though.
        rule_expr = timex.parse(rule)

        exp_timestamp = rule_expr(timestamp=datetime.now())

        # You can access the datetime for a Timestamp matcher with
        # .timestamp, .begin, or .end, as they will be the same.
        # For TimeRanges, .begin is the start of the range, .end is the
        # end of the range, and .timestamp is a synonym for .begin
        item.expiration = exp_timestamp.timestamp

```

## Using Time Expressions

Time expressions can represent a single timestamp, calculated according to
the expression, or a range of times between a beginning datetime and an end.
In either case the usage is the same:

* Call timex.parse() to get an expression object from your string.
* Call the expression with any values you need as keyword args.
  Note that there is a **default** variable, named _$timestamp_ that is
  always available to your expressions. If you don't supply a value for it
  as a keyword, then the value from _datetime.utcnow()_ is uesd.
* The above call gets you a Timestamp object or a TimeRange object,
  depending on whether the expression represents a range, or a single
  timestamp. Both of these have the same methods and attributes available.
  You can compare a datetime to these objects using the .match() method,
  or the _in_ operator (both will produce the same result), or access the
  calculated datetimes with the .timestamp, .begin or .end attributes.

## Time Expression Reference and Syntax

### Duration:

A Duration is simply a number with a unit attached, like so:
`6h` or `30m`. Durations can also be ganged together like so `6h 30m 15s`
Valid units are:

| Unit | Description |
|:----:| ------------|
|  y   | Year        |
| mo   | Month       |
|  d   | Day         |
|  h   | Hour        |
|  m   | Minute      |
|  s   | Second      |
| us   | Microsecond |

### Timestamp expression:

Expression that evaluates to a single datetime.

### TimeRange expression:

Expression that evaluates to a range of time, represented by a begin
datetime and an end datetime. Addition, subtraction, or replace operations
on a range will perform the same operation on both the begin and end of the
timerange. Ranges can be created using the `to` operator, or with the special
range functions.

### Special (a.k.a "pinned") Time Ranges:

Special time ranges are generated with the special range functions `hour`, `day`, `month` and `year`.
For example the expression `day($start)` represents "the full day containing time $start". These ranges
are "special" because they remember the timestamp they are created from, and will "wrap around" on addition,
subtraction and replace operations so the timestamp is still within that range.

For example: If `$start` is "2014-08-01 01:00:00", then `day($start)` will be the
range "2014-08-01 00:00:00" to "2014-08-02 00:00:00", but `day($start) + 6h` will be the
range "2014-07-31 00:00:00" to "2014-08-01 06:00:00", so it will still contain $start.

This wrapping of the range will occure as long as the Duration added,
subtracted, or replaced is not larger than the range itself.

Note that the argument to one of these functions can be any timestamp expression, and if no argument is supplied,
it will default to the default variable `$timestamp`. Also, if no argument is supplied, the parens are not required,
like so `day + 6h`.

### Basic Syntax:

| Syntax                    | Meaning                                                               |
| ------------------------- | --------------------------------------------------------------------- |
| $variablename             | Access value passed to expression as keyword arg.                     |
| ()                        | Parentheses can be used to group expressions together for precedence. |
| `expression` + `duration` | Add time to a timestamp or range.                                     |
| `expression` - `duration` | Subtract time from a timestamp or range.                              |
| `expression` @ `duration` | Replace operator for timestamp or range. Replaces component of datetime(s), similar to datetime's `replace` method |
| `timestamp1` to `timestamp2` | Create a time range beginning at `timestamp1` and ending at `timestamp2` |

