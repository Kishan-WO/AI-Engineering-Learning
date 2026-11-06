"""Day 2, task 4: Pydantic models for a messy "student enquiry" form."""

from typing import Self
import json
import re
from collections import Counter
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

Course = Literal["python", "ai", "web"]


def parse_budget(value: object) -> int:
    """Turn '5000', '₹25,000', '5k', 'Rs. 8,000' or 5000.0 into whole rupees."""
    if value is None or isinstance(value, bool):  # bool is an int subclass: True would become 1
        raise ValueError("budget must be a number")
    if isinstance(value, int | float):
        number = float(value)
    elif isinstance(value, str):
        text = re.sub(r"(?i)rs\.?|inr|₹|,|\s", "", value)
        multiplier = 1
        if text.lower().endswith("k"):
            multiplier, text = 1000, text[:-1]
        try:
            number = float(text) * multiplier
        except ValueError:
            raise ValueError(f"budget {value!r} is not a number like 5000 or 5k") from None
    else:
        raise ValueError(f"budget must be a number, got {type(value).__name__}")
    if not number.is_integer():
        raise ValueError("budget must be a whole number of rupees")
    return int(number)


def parse_phone(value: object) -> str:
    """Turn '+91 98765-43210', '(987) 654 3210' or '09876543210' into 10 digits."""
    if isinstance(value, int) and not isinstance(value, bool):
        value = str(value)
    if not isinstance(value, str):
        raise ValueError("phone must be text or digits")
    digits = re.sub(r"\D", "", value)
    if len(digits) == 14 and digits.startswith("0091"):
        digits = digits[4:]
    elif len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    if len(digits) != 10:
        raise ValueError(f"phone must have 10 digits, got {len(digits)}")
    if digits[0] not in "6789":
        raise ValueError("phone must start with 6, 7, 8 or 9")
    return digits


class Enquiry(BaseModel):
    """One student enquiry. All five fields are required; unknown keys are an error."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(min_length=2, max_length=50)
    phone: str
    course: Course
    city: str = Field(min_length=2, max_length=40)
    budget: int = Field(gt=0, le=1_000_000, description="Budget in INR")

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        if not re.fullmatch(r"[A-Za-z .'-]+", v):
            raise ValueError("name may contain only letters, spaces, dots, apostrophes and hyphens")
        return " ".join(v.split()).title()

    @field_validator("phone", mode="before")
    @classmethod
    def clean_phone(cls, v: object) -> str:
        return parse_phone(v)

    @field_validator("course", mode="before")
    @classmethod
    def clean_course(cls, v: object) -> object:
        return v.strip().lower() if isinstance(v, str) else v  # Literal still rejects bad values

    @field_validator("city")
    @classmethod
    def clean_city(cls, v: str) -> str:
        return " ".join(v.split()).title()

    @field_validator("budget", mode="before")
    @classmethod
    def clean_budget(cls, v: object) -> int:
        return parse_budget(v)

    @model_validator(mode="after")
    def ai_needs_budget(self) -> Self:
        if self.course == "ai" and self.budget < 5000:
            raise ValueError("the ai course needs a budget of at least 5000")
        return self


def process(rows: list[Any]) -> tuple[list[Enquiry], list[dict[str, Any]]]:
    """Validate every row. Returns (valid enquiries, failure records)."""
    valid: list[Enquiry] = []
    failures: list[dict[str, Any]] = []
    for number, row in enumerate(rows, start=1):
        try:
            valid.append(Enquiry.model_validate(row))
        except ValidationError as e:
            failures.append({"row": number, "data": row, "errors": e.errors()})
    return valid, failures


def loc_text(error: Any) -> str:
    return ".".join(str(part) for part in error["loc"]) or "(whole enquiry)"


def format_errors(failure: dict[str, Any]) -> list[str]:
    return [
        f"row {failure['row']}: {loc_text(err)}: {err['msg'].removeprefix('Value error, ')}"
        for err in failure["errors"]
    ]


### =============== DATA ===============

VALID_ROWS: list[dict[str, Any]] = [
    {"name": "  rAvI   kumar ", "phone": "98765-43210", "course": "Python ", "city": " pune", "budget": "5000"},
    {"name": "ANITA SHARMA", "phone": "+91 98765 43210", "course": "AI", "city": "MUMBAI", "budget": "₹25,000"},
    {"name": "Sunil", "phone": "(987) 654 3210", "course": "web", "city": "delhi", "budget": "5k"},
    {"name": "Meera Nair", "phone": "0091 9876543210", "course": "python", "city": "kochi", "budget": 5000.0},
    {"name": "o'neil patrick", "phone": "09876543210", "course": "web", "city": "New   Delhi", "budget": 12000},
    {"name": "Kiran Rao", "phone": 919876543210, "course": "ai", "city": "Hyderabad", "budget": "20k"},
    {"name": "Priya", "phone": "98765 43210", "course": "  PYTHON", "city": "chennai", "budget": "Rs. 8,000"},
    {"name": "Vikram Singh", "phone": "9876543210", "course": "web", "city": "jaipur", "budget": "1,00,000"},
    {"name": "Neha", "phone": "+919876543210", "course": "ai", "city": "Bangalore", "budget": "10K"},
    {"name": "Arjun Das", "phone": "98765.43210", "course": "python", "city": "kolkata", "budget": "  3000  "},
    {"name": "Sara Khan", "phone": "6123456789", "course": "web", "city": "lucknow", "budget": 999999},
    {"name": "Tina Dsouza", "phone": "7000000001", "course": "ai", "city": "goa", "budget": 5000},
]

# (row, the fields that should be reported as wrong)
INVALID_ROWS: list[tuple[Any, set[str]]] = [
    ({"name": "Ravi", "course": "python", "city": "pune", "budget": 5000}, {"phone"}),  # missing phone
    ({"name": "Ravi", "phone": "12345", "course": "python", "city": "pune", "budget": 5000}, {"phone"}),
    ({"name": "Ravi", "phone": "1234567890", "course": "python", "city": "pune", "budget": 5000}, {"phone"}),
    ({"name": "Ravi", "phone": "9876543210", "course": "java", "city": "pune", "budget": 5000}, {"course"}),
    ({"name": "Ravi", "phone": "9876543210", "course": "", "city": "pune", "budget": 5000}, {"course"}),
    ({"name": "R", "phone": "9876543210", "course": "web", "city": "pune", "budget": 5000}, {"name"}),
    ({"name": "R2D2", "phone": "9876543210", "course": "web", "city": "pune", "budget": 5000}, {"name"}),
    ({"name": "Ravi", "phone": "9876543210", "course": "web", "city": "pune", "budget": -100}, {"budget"}),
    ({"name": "Ravi", "phone": "9876543210", "course": "web", "city": "pune", "budget": "free"}, {"budget"}),
    ({"name": "Ravi", "phone": "9876543210", "course": "web", "city": "pune", "budget": None}, {"budget"}),
    ({"name": "Ravi", "phone": "9876543210", "course": "web", "city": "pune", "budget": 5_000_000}, {"budget"}),
    ({"name": "Ravi", "phone": "9876543210", "course": "web", "city": "pune", "budget": 5000, "email": "x@y.com"}, {"email"}),
    ({"name": "Ravi", "phone": "9876543210", "course": "web", "city": "", "budget": 5000}, {"city"}),
    ({"name": "A", "phone": "abc", "course": "go", "city": "", "budget": "-5"},
     {"name", "phone", "course", "city", "budget"}),  # five problems in one row
    ({"name": "Ravi", "phone": "9876543210", "course": "ai", "city": "pune", "budget": 2000}, {"(whole enquiry)"}),
    ({"name": "Ravi", "phone": "9876543210", "course": "web", "city": "pune", "budget": True}, {"budget"}),
    ({"name": "Ravi", "phone": None, "course": "web", "city": "pune", "budget": 5000}, {"phone"}),
    ("just a string, not a dict", {"(whole enquiry)"}),
]

ROWS: list[Any] = VALID_ROWS + [row for row, _ in INVALID_ROWS]


### =============== MAIN + TESTING ===============

if __name__ == "__main__":
    assert len(ROWS) == 30

    valid, failures = process(ROWS)

    print(f"Checked {len(ROWS)} rows: {len(valid)} valid, {len(failures)} invalid\n")

    print("--- one cleaned result (row 1) ---")
    print("before:", VALID_ROWS[0])
    print("after :", valid[0].model_dump(), "\n")

    print("--- every failure ---")
    type_counts: Counter[str] = Counter()
    for failure in failures:
        for line in format_errors(failure):
            print(line)
        type_counts.update(err["type"] for err in failure["errors"])

    print("\n--- error types ---")
    for error_type, count in type_counts.most_common():
        print(f"{count:3}  {error_type}")

    print("\n--- JSON schema an LLM would receive ---")
    print(json.dumps(Enquiry.model_json_schema(), indent=2))

    print("\n--- checks ---")

    # 1. a messy valid row gives exactly the cleaned values
    assert valid[0].model_dump() == {
        "name": "Ravi Kumar", "phone": "9876543210", "course": "python", "city": "Pune", "budget": 5000,
    }
    assert [e.budget for e in valid[:9]] == [5000, 25000, 5000, 5000, 12000, 20000, 8000, 100000, 10000]
    assert all(e.phone == "9876543210" for e in valid[:10])
    assert valid[4].name == "O'Neil Patrick" and valid[4].city == "New Delhi"
    print("1. messy valid rows are cleaned correctly: PASS")

    # 2. each invalid row fails on the field we intended
    assert len(failures) == len(INVALID_ROWS)
    for failure, (_, expected) in zip(failures, INVALID_ROWS, strict=True):
        found = {loc_text(err) for err in failure["errors"]}
        assert found == expected, f"row {failure['row']}: expected {expected}, got {found}"
    print("2. every invalid row fails on the intended field(s): PASS")

    # 3. several problems in one row are all reported
    five_problems = next(f for f in failures if len(f["errors"]) > 1)
    assert len(five_problems["errors"]) == 5
    print("3. a row with five problems reports five errors: PASS")

    # 4. totals
    assert len(valid) + len(failures) == 30 and len(valid) == 12 and len(failures) == 18
    print("4. 12 valid + 18 invalid = 30: PASS")

    # 5. model_dump has only the five fields
    assert set(valid[0].model_dump()) == {"name", "phone", "course", "city", "budget"}
    print("5. model_dump contains only the five fields: PASS")

    # helper functions on their own
    assert parse_budget("2.5k") == 2500 and parse_budget("Rs. 1,000") == 1000
    assert parse_phone("0091 98765 43210") == "9876543210"
    print("6. parse_budget / parse_phone helpers: PASS")

    print("\nall enquiry checks passed")
