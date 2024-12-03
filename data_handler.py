import json
import os

# Define the path to the data directory
DATA_DIR = 'data'

def read_json(file_name):
    """Read data from a JSON file."""
    try:
        with open(os.path.join(DATA_DIR, file_name), 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return None

def write_json(file_name, data):
    """Write data to a JSON file."""
    with open(os.path.join(DATA_DIR, file_name), 'w') as file:
        json.dump(data, file, indent=4)

def get_all_users():
    """Get all users from the users.json file."""
    return read_json('users.json') or {'users': []}

def save_users(users):
    """Save all users to the users.json file."""
    write_json('users.json', users)

def get_all_jobs():
    """Get all jobs from the jobs.json file."""
    return read_json('jobs.json') or {'jobs': []}

def save_jobs(jobs):
    """Save all jobs to the jobs.json file."""
    write_json('jobs.json', jobs)

def get_messages():
    """Get all messages from the messages.json file."""
    return read_json('messages.json') or {'messages': []}

def save_messages(messages):
    """Save all messages to the messages.json file."""
    write_json('messages.json', messages)

def get_results():
    """Get all results from the results.json file."""
    return read_json('results.json') or {'results': []}

def save_results(results):
    """Save all results to the results.json file."""
    write_json('results.json', results)

def get_notifications():
    """Get all notifications from the notifications.json file."""
    return read_json('notifications.json') or {'notifications': []}

def save_notifications(notifications):
    """Save all notifications to the notifications.json file."""
    write_json('notifications.json', notifications)

def get_test_data(job_id):
    """Get test data for a specific job from the test_data.json file."""
    test_data = read_json('test_data.json') or {'tests': []}
    for test in test_data['tests']:
        if test['job_id'] == job_id:
            return test['questions']
    return None

def save_test_data(test_data):
    """Save test data to the test_data.json file."""
    write_json('test_data.json', test_data)
