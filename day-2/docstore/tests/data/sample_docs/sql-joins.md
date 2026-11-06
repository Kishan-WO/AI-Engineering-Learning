# SQL Joins

A join combines rows from two tables based on a related column.

- An INNER JOIN returns only rows that match in both tables.
- A LEFT JOIN returns every row from the left table, with NULLs where there is no match.
- A FULL OUTER JOIN returns rows from both sides, matched where possible.

Always join on indexed columns, such as a foreign key, to keep queries fast.
