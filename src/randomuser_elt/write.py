"""Write API response text to CSV

Write response text from client to CSV in dbt/seeds directory, raise exceptions as appropriate
"""


def seed_response_csv(response):
    with open("dbt/seeds/randomuser.csv", "w") as f:
        f.write(response.text)
