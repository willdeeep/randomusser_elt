"""RandomUser 1K CSV extraction client.

1st Draft
"""

import requests

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

    with open("dbt/seeds/randomuser.csv", "w") as f:
        f.write(response.text)
