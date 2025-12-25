#!/usr/bin/env python3
"""
Metadata Helper Script for patatese Repository

This script provides utilities for managing repository metadata stored in metadata.json.
It supports viewing, getting, setting, and validating metadata fields.

Usage:
    python metadata_helper.py --view                    # View all metadata
    python metadata_helper.py --get <field_path>       # Get specific field
    python metadata_helper.py --set <field_path> <value> # Set specific field
    python metadata_helper.py --validate               # Validate metadata format
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional


class MetadataHelper:
    """Helper class for managing repository metadata."""

    def __init__(self, metadata_file: str = "metadata.json"):
        """Initialize the metadata helper.
        
        Args:
            metadata_file: Path to the metadata JSON file
        """
        self.metadata_file = Path(metadata_file)
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict[str, Any]:
        """Load metadata from the JSON file.
        
        Returns:
            Dictionary containing metadata
            
        Raises:
            FileNotFoundError: If metadata file doesn't exist
            json.JSONDecodeError: If metadata file is invalid JSON
        """
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Metadata file '{self.metadata_file}' not found.")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in metadata file: {e}")
            sys.exit(1)

    def _save_metadata(self) -> None:
        """Save metadata to the JSON file."""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
            f.write('\n')  # Add trailing newline

    def view_all(self) -> None:
        """Display all metadata in a formatted manner."""
        print(json.dumps(self.metadata, indent=2))

    def get_field(self, field_path: str) -> Optional[Any]:
        """Get a specific field from metadata using dot notation.
        
        Args:
            field_path: Dot-separated path to the field (e.g., 'project.name')
            
        Returns:
            The value of the field, or None if not found
        """
        keys = field_path.split('.')
        value = self.metadata
        
        try:
            for key in keys:
                # Handle array indices
                if '[' in key and ']' in key:
                    field_name = key[:key.index('[')]
                    index_str = key[key.index('[')+1:key.index(']')]
                    try:
                        index = int(index_str)
                    except ValueError:
                        print(f"Error: Invalid array index '{index_str}' in field path '{field_path}'. Index must be a number.")
                        return None
                    value = value[field_name][index]
                else:
                    value = value[key]
            return value
        except KeyError as e:
            print(f"Error: Field '{field_path}' not found in metadata. The key {e} does not exist.")
            return None
        except IndexError:
            print(f"Error: Array index out of range in field path '{field_path}'. Check that the index is valid.")
            return None
        except TypeError:
            print(f"Error: Type mismatch when accessing field path '{field_path}'. Check that you're not trying to index a non-list field.")
            return None

    def set_field(self, field_path: str, new_value: str) -> bool:
        """Set a specific field in metadata using dot notation.
        
        Args:
            field_path: Dot-separated path to the field (e.g., 'project.version')
            new_value: New value to set (will be parsed as JSON if possible)
            
        Returns:
            True if successful, False otherwise
        """
        # Try to parse the value as JSON (for numbers, booleans, objects, arrays)
        try:
            parsed_value = json.loads(new_value)
        except json.JSONDecodeError:
            # If it's not valid JSON, treat it as a string
            parsed_value = new_value

        keys = field_path.split('.')
        value = self.metadata
        
        try:
            # Navigate to the parent of the target field
            for key in keys[:-1]:
                if '[' in key and ']' in key:
                    field_name = key[:key.index('[')]
                    index_str = key[key.index('[')+1:key.index(']')]
                    try:
                        index = int(index_str)
                    except ValueError:
                        print(f"Error: Invalid array index '{index_str}' in field path '{field_path}'. Index must be a number.")
                        return False
                    value = value[field_name][index]
                else:
                    value = value[key]
            
            # Set the final field
            final_key = keys[-1]
            if '[' in final_key and ']' in final_key:
                field_name = final_key[:final_key.index('[')]
                index_str = final_key[final_key.index('[')+1:final_key.index(']')]
                try:
                    index = int(index_str)
                except ValueError:
                    print(f"Error: Invalid array index '{index_str}' in field path '{field_path}'. Index must be a number.")
                    return False
                value[field_name][index] = parsed_value
            else:
                value[final_key] = parsed_value
            
            self._save_metadata()
            print(f"Successfully updated '{field_path}' to: {parsed_value}")
            return True
            
        except KeyError as e:
            print(f"Error: Cannot set field '{field_path}'. The key {e} does not exist in the metadata structure.")
            return False
        except IndexError:
            print(f"Error: Array index out of range in field path '{field_path}'. Check that the index is valid.")
            return False
        except TypeError:
            print(f"Error: Type mismatch when accessing field path '{field_path}'. Check that you're not trying to index a non-list field.")
            return False

    def validate(self) -> bool:
        """Validate the metadata structure.
        
        Returns:
            True if metadata is valid, False otherwise
        """
        required_fields = [
            'project',
            'project.name',
            'project.version',
            'project.description',
            'maintainers',
            'license',
            'metadata_version'
        ]
        
        is_valid = True
        
        for field in required_fields:
            value = self.get_field(field)
            if value is None:
                print(f"Validation Error: Required field '{field}' is missing.")
                is_valid = False
        
        # Check that maintainers is a list
        if not isinstance(self.metadata.get('maintainers'), list):
            print("Validation Error: 'maintainers' must be a list.")
            is_valid = False
        
        # Check version format (basic check)
        version = self.get_field('project.version')
        if version and not isinstance(version, str):
            print("Validation Error: 'project.version' must be a string.")
            is_valid = False
        
        if is_valid:
            print("✓ Metadata validation passed!")
        else:
            print("✗ Metadata validation failed.")
        
        return is_valid


def main():
    """Main entry point for the metadata helper script."""
    parser = argparse.ArgumentParser(
        description='Manage repository metadata',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --view
  %(prog)s --get project.name
  %(prog)s --get maintainers[0].name
  %(prog)s --set project.version "2.0.0"
  %(prog)s --validate
        """
    )
    
    parser.add_argument('--view', action='store_true',
                        help='View all metadata')
    parser.add_argument('--get', metavar='FIELD',
                        help='Get a specific field (dot notation)')
    parser.add_argument('--set', nargs=2, metavar=('FIELD', 'VALUE'),
                        help='Set a specific field (dot notation)')
    parser.add_argument('--validate', action='store_true',
                        help='Validate metadata format')
    parser.add_argument('--file', default='metadata.json',
                        help='Path to metadata file (default: metadata.json)')
    
    args = parser.parse_args()
    
    # Show help if no arguments provided
    if not any([args.view, args.get, args.set, args.validate]):
        parser.print_help()
        sys.exit(0)
    
    # Initialize helper
    helper = MetadataHelper(args.file)
    
    # Execute requested operation
    if args.view:
        helper.view_all()
    
    if args.get:
        value = helper.get_field(args.get)
        if value is not None:
            if isinstance(value, (dict, list)):
                print(json.dumps(value, indent=2))
            else:
                print(value)
    
    if args.set:
        helper.set_field(args.set[0], args.set[1])
    
    if args.validate:
        is_valid = helper.validate()
        sys.exit(0 if is_valid else 1)


if __name__ == '__main__':
    main()
