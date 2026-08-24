# Task Completion Process

***My working process for completing this Assessment Task**

## Starting Point
I started by reviewing the [API documentation](https://randomuser.me/documentation) alongside the task instructions and used Postman to build an API call I that I thought ticked all the boxes:

```
https://randomuser.me/api/?format=csv&results=1000&seed=foobar&nat=gb&inc=id,gender,name,location,email,dob,registered
```

## Planning and Drafting a Spike
As the option to return the results as CSV simplified the **load** step, my plan is for a simple process.

### Planned Outline

```text
Extract CSV from API -> Load to dbt/seeds dir -> dbt seed -> dbt build/run -> SQLite DB
```

So I thought I'd start with a simple python extract/load to get to the CSV seed stage, then configure the dbt seed and model YAML files so build and run validates the type, completeness of all fields in all records, flagging any failures or nonconformance as it transforms the CSV into a normalised format - maybe [3nf](https://www.geeksforgeeks.org/dbms/third-normal-form-3nf/). I plan to use SQLite as a simple DB, so anyone can pull and run this on their machine.


So I wanted to keep the data extraction/load as simple as possible, leaving data validation of individual records for the `dbt seed` step.

I copied/edited `pyproject.toml` from a prior, similar projects, including the imports and settings for:
 - linting and code formatting with `ruff`.
 - type checking with `mypy`.
 - testing, including coverage, with `pytest`.

I used that as a template to set up my environment and iported packages, then made a first draft of the `client.py` [module](src/randomuser_elt/client.py):

```py
import process

return_columns = ["id", "gender", "name", "location", "email", "dob", "registered"]


def get_randomuser_response():
    url = "https://randomuser.me/api/"
    params = {
        "format": "csv",
        "results": "1000",
        "seed": "foobar",
        "nat": "gb",
        "inc": ",".join(return_columns),
    }
    response = requests.get(url, params=params)

    with open("test.csv", "w") as f:
        f.write(response.text)
```

This worked as a spike, but I needed to write the csv to the dbt seeds directory for my process above, plus it lacked any robustness, logging or error management, and had hardcoded variables so if I wanted to add another column to `inc` or remove/update the `nat` filter, I'd have to edit code directly.

## Invoke and tasks.py
to stop other users from having to copy paste commands with spoecific flags, or build out a dedicated cli, I like to use `invoke` with `subprocess` to standardise commands especially for dbt. I think the `tasks.py` file provides a clear, readable document of recommended bash commands as `subprocess` enables raw bash to be entered inline while still providing clear terminal feedback.

## Productionising

### Loading Variables
I copied across a settings template for `config.py` [here](src/randomuser_elt/config.py) from another project, and updated the variables. I also added a `.env` and `.env.example`. I know there's no secrets or keys in this project, but I'm still not going to commit `.env`.

I imported necessary `pydantic` items and used the `BaseSettings` class to specify the data types and defaults (if any) for the separate `ExtractSettings` and `DbtSettings` classes.

My choice on whether to default/Null or fail wwas based on what action I wanted in each case.
 - If the URL is missing I wanted a fail as that would mean nvironment variables weren't set.
 - If the `format` setting was missing I wanted it to default to `csv` as that is the only format this pipeline is se tto work with.
 - If other parameters were missing I wanted the API call to proceed with them as absent, so I or another user could choose to remove them if they didn't want them.

### Adapting client.py
I wanted the client module to remain as simple as possible, while  loading variables, managing some backoff/retry, and raising exceptions. I like using [tenacity](https://tenacity.readthedocs.io/en/latest/) for simplified, readable call management, so I added that import and instructed Claude on how I wanted it to adapt the spike.
