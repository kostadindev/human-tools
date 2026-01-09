# Conversation Testing Script

This script allows you to test the chatbot with predefined test cases and compare responses with and without the constitution.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure the agent API server is running:
```bash
python agent_api.py
```

## Usage

### Basic Usage

Run all tests with both constitution settings (default). The script will automatically toggle the constitution via the API:
```bash
python test_conversation.py test_cases.yaml
```

### Run with Specific Constitution File

```bash
python test_conversation.py test_cases.yaml --constitution-file cambridge_university_v1.txt
```

### Run Only With Constitution

```bash
python test_conversation.py test_cases.yaml --with-constitution
```

### Run Only Without Constitution

```bash
python test_conversation.py test_cases.yaml --without-constitution
```

### Custom API URL

```bash
python test_conversation.py test_cases.yaml --api-url http://localhost:8000
```

### Custom Output Directory

```bash
python test_conversation.py test_cases.yaml --output-dir my_results
```

## How It Works

1. **Load Test Cases**: The script reads test cases from a YAML file.
2. **Dynamic Toggling**: The script calls the API to enable/disable the constitution automatically.
3. **Run Tests**: For each test case, it sends the input to the chatbot API.
4. **Collect Responses**: It collects the full response for each test.
5. **Generate Comparison**: It creates side-by-side comparison reports.

## Test Case Format

Test cases are defined in YAML format (see `test_cases.yaml` for a complete example):

```yaml
allow_cases:
  - id: A1
    name: "Test name"
    category: ALLOW
    input: "User input text"
    expected:
      decision: ALLOW
```

## Output Files

The script generates three types of files in the output directory:

1. **Comparison Report** (`comparison_report_YYYYMMDD_HHMMSS.md`):
   - Side-by-side markdown table of all responses.
   - Ideal for quick manual review.

2. **JSON Results** (`test_results_YYYYMMDD_HHMMSS.json`):
   - Complete raw data in JSON format.
   - Useful for integration with other tools.

3. **CSV Report** (`comparison_report_YYYYMMDD_HHMMSS.csv`):
   - Tabular format for spreadsheet analysis (Excel, Google Sheets).

## Example Workflow

1. **Start the API Server**:
   ```bash
   python agent_api.py
   ```

2. **Run the Tests**:
   ```bash
   python test_conversation.py test_cases.yaml --both
   ```

## Notes

- The script **automatically toggles** the constitution via the API, so no manual restarts are required.
- Each test includes a small delay (0.5s) between requests.
- Timeout is set to 120 seconds per request.

