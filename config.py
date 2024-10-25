timeout = 10 # Set the default timeout value for all requests
retry_timeout = 10 # Set the retry timeout value for network errors
max_retries = 3 # Set the number of retries for network errors
github_token = ''
repo_list = [
    {'name': 'transformers',
     'owner': 'huggingface',
     'get_tags': False},   # https://github.com/huggingface/transformers
    {'name': 'pytorch',
     'owner': 'pytorch',
     'get_tags': False},       # https://github.com/pytorch/pytorch
    {'name': 'tensorflow',
     'owner': 'tensorflow',
     'get_tags': False},    # https://github.com/tensorflow/tensorflow
     ] 