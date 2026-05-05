import yaml
import json
import argparse
from pathlib import Path
def write_yaml(file_path, data):
    if isinstance(file_path, Path):
        file_path = str(file_path)
    with open(file_path, 'w') as file:
        yaml.safe_dump(data, file)
    
def load_json(file_path):
    if isinstance(file_path, Path):
        file_path = str(file_path)
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

script_dir = Path(__file__).parent

if __name__ == "__main__":
    """Read a list of yaml files and dump as json files.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+')
    args = parser.parse_args()

    for file in args.files:
        assert Path(file).exists(), f"{file} is not found."
        data = load_json(file)
        yaml_file_fn = file.rsplit('.', 1)[0] + '.yaml'
        write_yaml(yaml_file_fn, data)