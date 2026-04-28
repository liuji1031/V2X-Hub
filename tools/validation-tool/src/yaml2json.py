import yaml
import json
import argparse
from pathlib import Path
def read_yaml(file_path):
    if isinstance(file_path, Path):
        file_path = str(file_path)
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)
    
def dump_json(data, file_path):
    if isinstance(file_path, Path):
        file_path = str(file_path)
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

script_dir = Path(__file__).parent

if __name__ == "__main__":
    """Read a list of yaml files and dump as json files.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+')
    args = parser.parse_args()

    for file in args.files:
        data = read_yaml(script_dir.parent / "sample" / "yaml" / file)
        json_file_fn = file.rsplit('.', 1)[0] + '.json'
        dump_json(data, script_dir.parent / "sample" / json_file_fn)

