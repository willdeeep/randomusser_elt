{#
    Whole years elapsed between now and dob_column, floored -- i.e.
    floor((current_date - dob) / 365.25). Shared by mart_user_directory's
    `age` column and the drift-check test on dim_user.dob_age, so the same
    SQLite date arithmetic isn't duplicated in both places.
#}
{% macro age_in_years(dob_column) %}
    cast((julianday('now') - julianday({{ dob_column }})) / 365.25 as int)
{% endmacro %}
