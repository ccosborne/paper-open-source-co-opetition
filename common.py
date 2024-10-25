import random
import requests
import config
import time

# Function to handle rate limiting
def handle_rate_limit(headers):
    # Check if rate limit is reached
    rate_limit_remaining = int(headers.get('X-RateLimit-Remaining', '0'))
    if rate_limit_remaining == 0:
        rate_limit_reset = int(headers.get('X-RateLimit-Reset', '0'))
        current_time = int(time.time())
        if rate_limit_reset > current_time:
            min_wait_time = 30  # Minimum wait time in seconds
            max_wait_time = 60  # Maximum wait time in seconds
            wait_time = rate_limit_reset - current_time + random.randint(min_wait_time, max_wait_time)
            print(f"Rate limit reached. Waiting for {wait_time} seconds...")
            time.sleep(wait_time)

# Function to send a GET request with timeout and rate limit handling
def get_with_timeout(url, headers, params=None):
    retries = 0
    while retries < config.max_retries:
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 403:
                error_msg = response.json().get('message')
                print(f"Network error 403 occurred: {str(error_msg)}. Retrying...")
                continue
            response.raise_for_status()  # Raise an exception if the response contains an error status code
            handle_rate_limit(response.headers)  # Check if the rate limit is reached
            return response
        except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as e:
            print(f"Network error occurred: {str(e)}. Retrying...")
            retries += 1
            time.sleep(config.timeout)  # Apply the timeout in case of a network error
            continue
    print(f"Failed to retrieve data from {url} after {config.max_retries} retries.")
    return None
