import json
import os


class FileHandler:
    def __init__(self, file_path):
        self.file_path = file_path

    def read(self, as_json=False):
        """
        Reads the content of the file.

        Parameters:
        as_json (bool): If True, reads the file as JSON. If False, reads as plain text.

        Returns:
        str or dict: The content of the file. Returns a dictionary if reading as JSON, otherwise a string.

        Raises:
        FileNotFoundError: If the file does not exist.
        JSONDecodeError: If the file is specified as JSON but contains invalid JSON.
        """
        if not os.path.isfile(self.file_path):
            raise FileNotFoundError(f"The file {self.file_path} does not exist.")

        with open(self.file_path, 'r', encoding='utf-8') as file:
            if as_json:
                try:
                    return json.load(file)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Error decoding JSON from the file {self.file_path}: {e}")
            else:
                return file.read()

    def write(self, content, as_json=False):
        """
        Writes content to the file.

        Parameters:
        content (str or dict): The content to write to the file. Should be a dictionary if as_json=True, otherwise a string.
        as_json (bool): If True, writes the content as JSON. If False, writes as plain text.
        """
        with open(self.file_path, 'w', encoding='utf-8') as file:
            if as_json:
                json.dump(content, file, indent=4)
            else:
                file.write(content)


if __name__ == "__main__":
    # Create a FileHandler instance for a specific file path
    text_file_path = 'example.txt'
    json_file_path = 'example.json'

    # For text file operations
    text_handler = FileHandler(text_file_path)
    text_handler.write("This is a text file content.")
    print(text_handler.read())  # Read as plain text

    # For JSON file operations
    json_handler = FileHandler(json_file_path)
    data = {"name": "Alice", "age": 30, "city": "New York"}
    json_handler.write(data, as_json=True)  # Write as JSON
    print(json_handler.read(as_json=True))  # Read as JSON


