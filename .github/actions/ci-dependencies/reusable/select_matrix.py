"""Select a review environment from an expanded GitHub Actions matrix."""

import itertools
import json
import sys


def matches(row, fields):
    return all(key in row and row[key] == value for key, value in fields.items())


def expand(matrix):
    axes = {
        key: value for key, value in matrix.items() if key not in ("include", "exclude")
    }
    if any(not isinstance(values, list) or not values for values in axes.values()):
        raise ValueError("matrix axes must be non-empty lists")
    original = (
        [dict(zip(axes, values)) for values in itertools.product(*axes.values())]
        if axes
        else []
    )
    original = [
        row
        for row in original
        if not any(matches(row, excluded) for excluded in matrix.get("exclude", []))
    ]
    rows = [row.copy() for row in original]
    for addition in matrix.get("include", []):
        compatible = [
            index
            for index, row in enumerate(original)
            if all(
                key not in row or row[key] == value for key, value in addition.items()
            )
        ]
        if compatible:
            for index in compatible:
                rows[index].update(addition)
        else:
            rows.append(addition.copy())
    return rows


def main():
    try:
        matrix = json.load(sys.stdin)
        rows = expand(matrix)
        defaults = [row for row in rows if row.get("review_default") is True]
        if len(defaults) != 1:
            raise ValueError("matrix must have exactly one review_default row")
        if len(sys.argv) > 1:
            override = json.loads(sys.argv[1])
            if not isinstance(override, dict) or not override:
                raise ValueError("override must identify a valid matrix row")
            candidates = [row for row in rows if matches(row, override)]
            if len(candidates) != 1:
                raise ValueError("override must select exactly one valid matrix row")
            selected = candidates[0]
        else:
            selected = defaults[0]
        print(json.dumps(selected, sort_keys=True))
    except (ValueError, TypeError, AttributeError) as error:
        print(f"matrix selection: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
