## v0.6.0 (2024-12-09)

### Feat

- **transx**: Add context management and instance caching for TransX
- **transx**: Add context management and instance caching for TransX

### Refactor

- **core**: Improve locale handling and add new interpreters for nested templates and environment variables
- **core**: Refactor string formatting and exception handling

## v0.5.1 (2024-12-06)

### Refactor

- **core, api**: Update variable names and string decoding methods
- **core**: Refactor translation loading and MO file handling - Use explicit encoding and updated logging - Optimize MO file reading and add hash table for faster lookups

## v0.5.0 (2024-12-06)

### Feat

- **translator**: Add setter for current locale and update tr method with context parameter
- **interpreter**: Add EnvironmentVariableInterpreter to support environment variables

### Refactor

- **api**: Refactor import statements in mo.py
- **core**: Refactor locale switching and translation loading logic

## v0.4.0 (2024-12-05)

### Feat

- **cli**: Add translate command with support for multiple languages and specific files

### Refactor

- **filesystem**: Update file read/write functions to use explicit encoding and add gitignore handling

## v0.3.0 (2024-12-05)

### Feat

- **cli**: Add list command to display available locales
- **translator**: Add French locale messages.mo file
- **core,docs**: Add available_locales property and update README with usage example
- **translator**: Use centralized language list for translation workflows
- **cli**: Enhance command line interface with improved examples and default values

### Refactor

- **api**: Refactor header comment and request headers usage

## v0.2.2 (2024-12-04)

### Refactor

- **interpreter**: Refactor import statements for clarity and consistency
- **interpreter**: Improve text type handling and error handling in TextTypeInterpreter

## v0.2.1 (2024-12-04)

### Fix

- fix entry point for transx CLI to main function.

## v0.2.0 (2024-12-04)

### Feat

- **transx/api**: Add TextInterpreter and related classes for text processing
- **examples**: Add test case for current username translation
- **cli,api**: Add PotUpdater and improve error handling in CLI commands

### Fix

- **cli,core**: improve error handling and logging in translation commands

### Refactor

- **examples**: Refactor import statements for clarity and consistency
- **examples**: Refactor import statements and translation workflow examples for clarity and consistency
- **examples**: Update language codes and improve compatibility in examples
- **transx/api/locale**: Improve language code normalization logic
- **examples**: Refactor import statements for clarity and consistency
- **examples**: Refactor translation workflow examples for clarity and consistency
- **examples**: Refactor translation workflow examples
- improve code organization and lint configuration
- **examples**: Refactor translation workflow examples

## v0.1.0 (2024-12-01)

### Feat

- **transx**: add TransX translation framework
