import time

from openai import OpenAI, AssistantEventHandler
import os
import sqlite3
from typing_extensions import override
import pandas as pd

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def initialize_sqlite_db(db_path='nlp_sql.db'):
    # Connect to the SQLite database
    connection = sqlite3.connect(db_path)
    team_df = pd.read_csv('data/teams.csv')
    team_df.to_sql('Team', connection, if_exists='replace', index=False)

    experiment_df = pd.read_csv('data/experiments.csv')
    experiment_df.to_sql('Experiment', connection, if_exists='replace', index=False)

    laboratory_df = pd.read_csv('data/laboratories.csv')
    laboratory_df.to_sql('Laboratory', connection, if_exists='replace', index=False)

    instrument_df = pd.read_csv('data/instruments.csv')
    instrument_df.to_sql('Instrument', connection, if_exists='replace', index=False)

    scientist_df = pd.read_csv('data/scientists.csv')
    scientist_df.to_sql('Scientist', connection, if_exists='replace', index=False)


    # Commit the changes
    connection.commit()

    # Close the connection
    connection.close()

    print("Database initialized successfully!")



# openAI client execution code from openAI documentation
def get_sql_query(natural_language_query):
    # Send the natural language query to OpenAI

    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        stream=True,
        messages = [{"role": "system", "content": """You are a database assistant.
        
I have a SQLite database with the following schema:
     
Team	
ID	char(8)
Name	varchar(30)
TeamLeadID	char(8)
LabID	char(8)

Experiment	
ID	char(8)
ScientistID	char(8)
Name	varchar(30)
Write Up	varchar(10000)
InstrumentID	char(8)
	
Laboratory	
ID	char(8)
Address	varchar(30)
BioSafety Level	tinyint unsigned
Name	varchar (30)

Instrument	
ID	type
Name	type
LabID	char(8)

Scientist	
ID	char(8)
FirstName	varchar(30)
LastName	varchar(30)
Salary	float(5,2)
TeamID	char(8)

    """},
    {"role": "user", "content": f"""Translate the following natural language femail to SQL: {natural_language_query}
    respond ONLY with the SQL query. Avoid using JOINs if possible, and do not use aliases.
    
    For example, if the user says "Show me all the teams", you should respond "SELECT * FROM Team;".
    """}
    ]
    )

    responseList = []
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            responseList.append(chunk.choices[0].delta.content)

    result = "".join(responseList)
    result = result.strip("```")
    result = result.strip("\n")
    result = result.strip("sql")
    return result

def openai_friendly_response_for_output(sql_query, sql_results):
    # Send the natural language query to OpenAI
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        stream=True,
        messages = [{"role": "system", "content": """You are a database assistant. Write a friendly response to the user based on the SQL query and results you received.
        Don't start your response with "Hello!"""
    },
    {"role": "user", "content": f"Query: {sql_query}"},
    {"role": "user", "content": f"Results: {sql_results}"}
    ]
    )

    responseList = []
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            responseList.append(chunk.choices[0].delta.content)

    result = "".join(responseList)
    return result



# Function to execute the SQL query on the SQLite database
def execute_sql_query(sql_query, db_path='nlp_sql.db'):
    # Connect to the SQLite database
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    output = None
    try:
        # Execute the SQL query
        cursor.execute(sql_query)

        # Fetch all results if it's a SELECT query
        if sql_query.lower().startswith("select"):
            results = cursor.fetchall()
            output = results
            # Print the results
            for row in results:
                print(row)
        else:
            # Commit changes for non-SELECT queries (INSERT, UPDATE, DELETE)
            connection.commit()

        print("Query executed successfully!")
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the connection
        connection.close()
    return output

# Main function to run the script
def main():
    # Ask the user for a natural language query
    natural_language_query = input("Enter your query in natural language: ")

    # Convert the natural language query into a SQL query
    initialize_sqlite_db()
    # sql_query = "SELECT * FROM Scientist WHERE TeamID = 'Team_1';"
    sql_query = get_sql_query(natural_language_query)

    print(f"Generated SQL Query: {sql_query}")

    # Execute the generated SQL query
    sql_result = execute_sql_query(sql_query)

    # Generate a friendly response based on the SQL query and results
    friendly_response = openai_friendly_response_for_output(sql_query, sql_result)
    print(f"Friendly Response: {friendly_response}")


if __name__ == "__main__":
    main()
